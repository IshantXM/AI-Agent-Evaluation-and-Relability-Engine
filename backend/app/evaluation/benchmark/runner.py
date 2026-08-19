from __future__ import annotations

from pathlib import Path

from ..core.models import AgentTrace
from ..orchestration.pipeline import EvaluationPipeline
from .corpus import BenchmarkCorpus
from .models import (
    BenchmarkCase,
    BenchmarkCaseResult,
    BenchmarkEvaluationResult,
    EvaluationExpectation,
)


class BenchmarkRunner:
    """
    Execute benchmark cases against the production evaluation pipeline.

    Responsibilities:
    - resolve benchmark trace fixtures
    - execute the existing EvaluationPipeline
    - compare evaluator outputs against benchmark ground truth
    - produce deterministic benchmark results

    Non-responsibilities:
    - evaluator implementation
    - consensus calculation
    - reliability calculation
    - benchmark aggregation
    """

    def __init__(
        self,
        *,
        pipeline: EvaluationPipeline,
        trace_directory: str | Path,
    ) -> None:
        self.pipeline = pipeline
        self.trace_directory = Path(trace_directory)

    async def run_case(
        self,
        case: BenchmarkCase,
    ) -> BenchmarkCaseResult:
        """Execute and score a single benchmark case."""

        trace_path = self.trace_directory / case.trace_file
        trace = self._load_trace(trace_path)

        pipeline_result = await self.pipeline.evaluate(trace)

        actual_by_evaluator = {
            result.evaluator: result
            for result in pipeline_result.evaluations
        }

        benchmark_results = [
            self._evaluate_expectation(
                evaluator=evaluator,
                expectation=expectation,
                actual=actual_by_evaluator.get(evaluator),
            )
            for evaluator, expectation in (
                case.expected_evaluations.items()
            )
        ]

        case_passed = bool(benchmark_results) and all(
            result.passed
            for result in benchmark_results
        )

        return BenchmarkCaseResult(
            case_id=case.case_id,
            run_id=trace.run_id,
            passed=case_passed,
            evaluations=benchmark_results,
            metadata={
                "category": case.category,
                "difficulty": case.difficulty,
                "trace_file": case.trace_file,
            },
        )

    async def run(
        self,
        corpus: BenchmarkCorpus,
        case_ids: list[str] | None = None,
    ) -> list[BenchmarkCaseResult]:
        """
        Execute selected benchmark cases.

        If ``case_ids`` is omitted, execute the entire corpus.
        """

        return [
            await self.run_case(case)
            for case in corpus.select(case_ids)
        ]

    @classmethod
    def _evaluate_expectation(
        cls,
        *,
        evaluator: str,
        expectation: EvaluationExpectation | dict[str, object],
        actual,
    ) -> BenchmarkEvaluationResult:
        """
        Compare one evaluator result against benchmark ground truth.

        ``model_copy(update=...)`` can bypass nested Pydantic validation.
        Normalize the expectation at this boundary so the execution layer
        always operates on a validated domain model.
        """

        expectation = cls._normalize_expectation(expectation)

        if actual is None:
            return BenchmarkEvaluationResult(
                evaluator=evaluator,
                expected_verdict=expectation.verdict,
                actual_verdict="MISSING",
                expected_score_min=expectation.min_score,
                expected_score_max=expectation.max_score,
                actual_score=0.0,
                passed=False,
                score_error=None,
            )

        score_error = abs(
            actual.score
            - cls._expected_score(
                expectation=expectation,
                actual_score=actual.score,
            )
        )

        passed = cls._matches_expectation(
            expectation=expectation,
            actual_verdict=actual.verdict,
            actual_score=actual.score,
        )

        return BenchmarkEvaluationResult(
            evaluator=evaluator,
            expected_verdict=expectation.verdict,
            actual_verdict=actual.verdict,
            expected_score_min=expectation.min_score,
            expected_score_max=expectation.max_score,
            actual_score=actual.score,
            passed=passed,
            score_error=round(score_error, 4),
        )

    @staticmethod
    def _normalize_expectation(
        expectation: EvaluationExpectation | dict[str, object],
    ) -> EvaluationExpectation:
        """
        Normalize a benchmark expectation into its domain model.

        This protects the runner from unvalidated nested mappings while
        preserving strict Pydantic validation and ``extra='forbid'``.
        """

        if isinstance(expectation, EvaluationExpectation):
            return expectation

        return EvaluationExpectation.model_validate(
            expectation
        )

    @staticmethod
    def _load_trace(path: Path) -> AgentTrace:
        if not path.exists():
            raise FileNotFoundError(
                f"Benchmark trace not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Benchmark trace path is not a file: {path}"
            )

        return AgentTrace.model_validate_json(
            path.read_text(
                encoding="utf-8"
            )
        )

    @staticmethod
    def _matches_expectation(
        *,
        expectation: EvaluationExpectation,
        actual_verdict: str,
        actual_score: float,
    ) -> bool:
        if actual_verdict != expectation.verdict:
            return False

        if (
            expectation.min_score is not None
            and actual_score < expectation.min_score
        ):
            return False

        if (
            expectation.max_score is not None
            and actual_score > expectation.max_score
        ):
            return False

        return True

    @staticmethod
    def _expected_score(
        *,
        expectation: EvaluationExpectation,
        actual_score: float,
    ) -> float:
        if expectation.min_score is not None:
            return expectation.min_score

        if expectation.max_score is not None:
            return expectation.max_score

        return actual_score