from __future__ import annotations

import asyncio
from collections.abc import Sequence
from uuid import uuid4

from ..core.models import AgentTrace, EvaluationResult
from ..orchestration.orchestrator import EvaluationOrchestrator

from .metrics import (
    calculate_score_delta,
    classify_impact,
    least_impactful_evaluator,
    most_impactful_evaluator,
)
from .models import (
    AblationCase,
    AblationCaseResult,
    AblationReport,
)


class AblationRunner:
    """
    Executes leave-one-evaluator-out reliability experiments.

    Baseline:
        Run the complete evaluator set.

    Ablation:
        Remove exactly one evaluator and rerun evaluation.

    The runner is intentionally independent of individual evaluator
    implementations.
    """

    def __init__(
        self,
        orchestrator: EvaluationOrchestrator,
    ) -> None:
        self.orchestrator = orchestrator

    async def run(
        self,
        trace: AgentTrace,
        *,
        evaluators: Sequence[str] | None = None,
        parallel: bool = True,
    ) -> AblationReport:
        """
        Execute an ablation study.

        Args:
            trace:
                Agent execution trace.

            evaluators:
                Evaluators to include in the study.
                If omitted, all registered evaluators are used.

            parallel:
                Whether independent ablation experiments should
                execute concurrently.

        Returns:
            Aggregated AblationReport.
        """

        evaluator_names = list(
            evaluators
            if evaluators is not None
            else self.orchestrator.registry.list()
        )

        if not evaluator_names:
            raise ValueError(
                "Cannot run ablation without evaluators."
            )

        # ---------------------------------------------------------
        # Baseline
        # ---------------------------------------------------------

        baseline_results = await self.orchestrator.evaluate(
            trace,
            evaluators=evaluator_names,
        )

        baseline_score = self._calculate_score(
            baseline_results
        )

        baseline_case_count = len(
            [
                result
                for result in baseline_results
                if result.evaluator in evaluator_names
            ]
        )

        # ---------------------------------------------------------
        # Construct experiments
        # ---------------------------------------------------------

        cases = [
            AblationCase(
                case_id=str(uuid4()),
                run_id=trace.run_id,
                evaluator_to_remove=evaluator,
                baseline_score=baseline_score,
                baseline_evaluator_count=baseline_case_count,
                metadata={
                    "experiment": "leave_one_evaluator_out",
                },
            )
            for evaluator in evaluator_names
        ]

        # ---------------------------------------------------------
        # Execute experiments
        # ---------------------------------------------------------

        if parallel:
            results = await asyncio.gather(
                *(
                    self._run_case(
                        trace,
                        case,
                        evaluator_names,
                    )
                    for case in cases
                )
            )
        else:
            results = []

            for case in cases:
                results.append(
                    await self._run_case(
                        trace,
                        case,
                        evaluator_names,
                    )
                )

        # ---------------------------------------------------------
        # Aggregate
        # ---------------------------------------------------------

        return AblationReport(
            run_id=trace.run_id,
            baseline_score=baseline_score,
            baseline_evaluator_count=baseline_case_count,
            results=results,
            most_impactful_evaluator=most_impactful_evaluator(
                results
            ),
            least_impactful_evaluator=least_impactful_evaluator(
                results
            ),
            metadata={
                "experiment": "leave_one_evaluator_out",
                "evaluators_tested": len(evaluator_names),
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
    ) -> AblationCaseResult:
        """
        Execute a single leave-one-out experiment.
        """

        removed = case.evaluator_to_remove

        remaining = [
            evaluator
            for evaluator in evaluator_names
            if evaluator != removed
        ]

        try:
            ablated_results = await self.orchestrator.evaluate(
                trace,
                evaluators=remaining,
            )

            ablated_score = self._calculate_score(
                ablated_results
            )

            delta = calculate_score_delta(
                case.baseline_score,
                ablated_score,
            )

            direction = classify_impact(delta)

            evaluation_ids = [
                result.evaluation_id
                for result in ablated_results
            ]

            return AblationCaseResult(
                case_id=case.case_id,
                run_id=trace.run_id,
                evaluator_removed=removed,
                status="COMPLETED",
                baseline_score=case.baseline_score,
                ablated_score=ablated_score,
                score_delta=delta,
                impact_direction=direction,
                baseline_evaluator_count=case.baseline_evaluator_count,
                ablated_evaluator_count=len(
                    ablated_results
                ),
                evaluation_ids=evaluation_ids,
                metadata={
                    "remaining_evaluators": remaining,
                },
            )

        except Exception as exc:
            return AblationCaseResult(
                case_id=case.case_id,
                run_id=trace.run_id,
                evaluator_removed=removed,
                status="FAILED",
                baseline_score=case.baseline_score,
                ablated_score=None,
                score_delta=None,
                impact_direction=None,
                baseline_evaluator_count=case.baseline_evaluator_count,
                ablated_evaluator_count=None,
                evaluation_ids=[],
                error=(
                    f"{type(exc).__name__}: {exc}"
                ),
                metadata={
                    "remaining_evaluators": remaining,
                },
            )

    @staticmethod
    def _calculate_score(
        results: Sequence[EvaluationResult],
    ) -> float:
        """
        Calculate reliability score from evaluator results.

        ERROR results are excluded because an evaluator execution
        failure is not evidence that the agent itself performed badly.
        """

        valid_results = [
            result
            for result in results
            if result.verdict != "ERROR"
        ]

        if not valid_results:
            return 0.0

        return round(
            sum(result.score for result in valid_results)
            / len(valid_results),
            4,
        )