from __future__ import annotations

import asyncio
import statistics
from collections.abc import Sequence
from uuid import uuid4

from ..core.models import AgentTrace, EvaluationResult
from ..orchestration.orchestrator import EvaluationOrchestrator

from .metrics import (
    calculate_relative_impact,
    calculate_score_delta,
    classify_impact,
    least_impactful_evaluator,
    most_impactful_evaluator,
)
from .models import (
    AblationCase,
    AblationCaseResult,
    AblationReport,
    AblationTrialResult,
)


class AblationRunner:
    """Execute leave-one-evaluator-out reliability experiments."""

    def __init__(self, orchestrator: EvaluationOrchestrator) -> None:
        self.orchestrator = orchestrator

    async def run(
        self,
        trace: AgentTrace,
        *,
        evaluators: Sequence[str] | None = None,
        parallel: bool = True,
        trials: int = 1,
        max_concurrency: int | None = None,
    ) -> AblationReport:
        """Run a baseline and one or more leave-one-out experiments."""
        if trials < 1:
            raise ValueError("trials must be at least 1.")
        if max_concurrency is not None and max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1.")

        evaluator_names = list(
            evaluators
            if evaluators is not None
            else self.orchestrator.registry.list()
        )
        self._validate_evaluators(evaluator_names)

        baseline_results = await self.orchestrator.evaluate(
            trace,
            evaluators=evaluator_names,
        )
        baseline_score = self._calculate_score(baseline_results)
        cases = [
            AblationCase(
                case_id=str(uuid4()),
                run_id=trace.run_id,
                evaluator_to_remove=evaluator,
                baseline_score=baseline_score,
                baseline_evaluator_count=len(baseline_results),
                metadata={
                    "experiment": "leave_one_evaluator_out",
                    "methodology": "leave_one_evaluator_out",
                    "methodology_version": "1.1",
                    "evaluator_order": evaluator_names,
                    "parallel": parallel,
                    "max_concurrency": max_concurrency,
                    "adversarial_scenario_count": 0,
                    "trial_count": trials,
                },
            )
            for evaluator in evaluator_names
        ]

        semaphore = asyncio.Semaphore(
            max_concurrency or len(cases)
        )

        async def run_case(case: AblationCase) -> AblationCaseResult:
            async with semaphore:
                return await self._run_case(
                    trace,
                    case,
                    evaluator_names,
                    trials,
                )

        if parallel:
            results = await asyncio.gather(
                *(run_case(case) for case in cases)
            )
        else:
            results = []
            for case in cases:
                results.append(await run_case(case))

        return AblationReport(
            run_id=trace.run_id,
            baseline_score=baseline_score,
            baseline_evaluator_count=len(baseline_results),
            results=results,
            most_impactful_evaluator=most_impactful_evaluator(results),
            least_impactful_evaluator=least_impactful_evaluator(results),
            metadata={
                "experiment": "leave_one_evaluator_out",
                "evaluators": evaluator_names,
                "evaluator_order": evaluator_names,
                "removed_evaluators": evaluator_names,
                "methodology": "leave_one_evaluator_out",
                "methodology_version": "1.1",
                "parallel": parallel,
                "max_concurrency": max_concurrency,
                "adversarial_scenario_count": 0,
                "trial_count": trials,
                "completed": sum(
                    result.status == "COMPLETED"
                    for result in results
                ),
                "failed": sum(
                    result.status == "FAILED"
                    for result in results
                ),
            },
        )

    async def _run_case(
        self,
        trace: AgentTrace,
        case: AblationCase,
        evaluator_names: list[str],
        trials: int,
    ) -> AblationCaseResult:
        removed = case.evaluator_to_remove
        remaining = [
            evaluator
            for evaluator in evaluator_names
            if evaluator != removed
        ]
        trial_results: list[AblationTrialResult] = []
        scores: list[float] = []
        evaluation_ids: list[str] = []

        for trial in range(1, trials + 1):
            try:
                results = await self.orchestrator.evaluate(
                    trace,
                    evaluators=remaining,
                )
                execution_errors = [
                    result
                    for result in results
                    if result.verdict == "ERROR"
                ]
                if execution_errors:
                    raise RuntimeError(
                        self._format_evaluator_error(
                            execution_errors[0]
                        )
                    )

                score = self._calculate_score(results)
                trial_ids = [
                    result.evaluation_id for result in results
                ]
                trial_results.append(
                    AblationTrialResult(
                        trial=trial,
                        status="COMPLETED",
                        score=score,
                        evaluation_ids=trial_ids,
                    )
                )
                scores.append(score)
                evaluation_ids.extend(trial_ids)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                trial_results.append(
                    AblationTrialResult(
                        trial=trial,
                        status="FAILED",
                        error=error,
                    )
                )
                return AblationCaseResult(
                    case_id=case.case_id,
                    run_id=trace.run_id,
                    evaluator_removed=removed,
                    status="FAILED",
                    baseline_score=case.baseline_score,
                    baseline_evaluator_count=case.baseline_evaluator_count,
                    evaluation_ids=evaluation_ids,
                    trial_results=trial_results,
                    trial_count=trials,
                    error=error,
                    metadata={
                        "remaining_evaluators": remaining,
                    },
                )

        mean_score = round(statistics.fmean(scores), 4)
        score_delta = calculate_score_delta(
            case.baseline_score,
            mean_score,
        )
        return AblationCaseResult(
            case_id=case.case_id,
            run_id=trace.run_id,
            evaluator_removed=removed,
            status="COMPLETED",
            baseline_score=case.baseline_score,
            ablated_score=mean_score,
            score_delta=score_delta,
            relative_impact=calculate_relative_impact(
                case.baseline_score,
                mean_score,
            ),
            impact_direction=classify_impact(score_delta),
            baseline_evaluator_count=case.baseline_evaluator_count,
            ablated_evaluator_count=len(remaining),
            evaluation_ids=evaluation_ids,
            trial_results=trial_results,
            trial_count=trials,
            mean_score=mean_score,
            standard_deviation=round(statistics.pstdev(scores), 4),
            minimum_score=min(scores),
            maximum_score=max(scores),
            metadata={
                "remaining_evaluators": remaining,
            },
        )

    def _validate_evaluators(self, evaluator_names: list[str]) -> None:
        if not evaluator_names:
            raise ValueError("Cannot run ablation without evaluators.")
        if len(set(evaluator_names)) != len(evaluator_names):
            raise ValueError("Evaluator names must be unique.")
        unknown = [
            name
            for name in evaluator_names
            if name not in self.orchestrator.registry
        ]
        if unknown:
            raise ValueError(
                "Unknown evaluator names: " + ", ".join(unknown)
            )

    @staticmethod
    def _format_evaluator_error(result: EvaluationResult) -> str:
        error_type = result.metadata.get(
            "error_type",
            "EvaluatorExecutionError",
        )
        return f"{error_type}: {result.summary}"

    @staticmethod
    def _calculate_score(
        results: Sequence[EvaluationResult],
    ) -> float:
        valid_results = [
            result
            for result in results
            if result.verdict != "ERROR"
        ]
        if not valid_results:
            raise RuntimeError(
                "Cannot calculate an ablation score without valid results."
            )
        return round(
            sum(result.score for result in valid_results)
            / len(valid_results),
            4,
        )
