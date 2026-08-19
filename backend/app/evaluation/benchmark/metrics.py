from __future__ import annotations

from collections import defaultdict
from statistics import fmean
from typing import Iterable

from .models import BenchmarkCaseResult, BenchmarkSummary


class BenchmarkMetrics:
    """
    Deterministic aggregation engine for benchmark results.

    Responsibilities:
    - aggregate case-level outcomes
    - aggregate evaluator-level outcomes
    - calculate score error
    - calculate category/difficulty breakdowns
    - produce a stable BenchmarkSummary

    Non-responsibilities:
    - executing benchmark cases
    - loading traces
    - running evaluators
    - modifying benchmark results
    """

    SCORE_PRECISION = 4

    @classmethod
    def summarize(
        cls,
        results: Iterable[BenchmarkCaseResult],
    ) -> BenchmarkSummary:
        """
        Aggregate benchmark case results into a summary.

        The input may be any iterable. Results are materialized once
        so generators are handled safely and deterministically.
        """

        materialized = tuple(results)

        total_cases = len(materialized)
        passed_cases = sum(
            result.passed
            for result in materialized
        )
        failed_cases = total_cases - passed_cases

        evaluations = tuple(
            evaluation
            for result in materialized
            for evaluation in result.evaluations
        )

        total_evaluations = len(evaluations)
        passed_evaluations = sum(
            evaluation.passed
            for evaluation in evaluations
        )

        case_accuracy = cls._ratio(
            passed_cases,
            total_cases,
        )

        evaluation_accuracy = cls._ratio(
            passed_evaluations,
            total_evaluations,
        )

        mean_score_error = cls._mean_score_error(
            evaluations
        )

        return BenchmarkSummary(
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            case_accuracy=case_accuracy,
            total_evaluations=total_evaluations,
            passed_evaluations=passed_evaluations,
            evaluation_accuracy=evaluation_accuracy,
            mean_score_error=mean_score_error,
            metadata={
                "categories": cls._group_breakdown(
                    materialized,
                    key=lambda result: result.metadata.get(
                        "category",
                        "unknown",
                    ),
                ),
                "difficulties": cls._group_breakdown(
                    materialized,
                    key=lambda result: result.metadata.get(
                        "difficulty",
                        "unknown",
                    ),
                ),
            },
        )

    @classmethod
    def _mean_score_error(
        cls,
        evaluations,
    ) -> float:
        """
        Calculate mean numerical score error.

        Missing evaluator results have ``score_error=None`` and are
        excluded because there is no actual score to compare.
        """

        errors = tuple(
            evaluation.score_error
            for evaluation in evaluations
            if evaluation.score_error is not None
        )

        if not errors:
            return 0.0

        return cls._round(
            fmean(errors)
        )

    @staticmethod
    def _ratio(
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator == 0:
            return 0.0

        return round(
            numerator / denominator,
            BenchmarkMetrics.SCORE_PRECISION,
        )

    @classmethod
    def _round(
        cls,
        value: float,
    ) -> float:
        return round(
            float(value),
            cls.SCORE_PRECISION,
        )

    @classmethod
    def _group_breakdown(
        cls,
        results: tuple[BenchmarkCaseResult, ...],
        *,
        key,
    ) -> dict[str, dict[str, object]]:
        """
        Build deterministic case-level breakdowns.

        Each group reports:
        - total cases
        - passed cases
        - failed cases
        - accuracy
        """

        grouped: dict[
            str,
            list[BenchmarkCaseResult],
        ] = defaultdict(list)

        for result in results:
            group = str(key(result))
            grouped[group].append(result)

        return {
            group: cls._summarize_group(
                group_results
            )
            for group, group_results in sorted(
                grouped.items()
            )
        }

    @classmethod
    def _summarize_group(
        cls,
        results: list[BenchmarkCaseResult],
    ) -> dict[str, object]:
        total = len(results)
        passed = sum(
            result.passed
            for result in results
        )

        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "accuracy": cls._ratio(
                passed,
                total,
            ),
        }