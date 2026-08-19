from __future__ import annotations

from collections.abc import Iterable

from .models import (
    AblationCaseResult,
    ImpactDirection,
)


def calculate_score_delta(
    baseline_score: float,
    ablated_score: float,
) -> float:
    """
    Calculate the change in reliability after removing an evaluator.

    Positive delta:
        Removing evaluator improved the score.

    Negative delta:
        Removing evaluator reduced the score.

    Zero:
        No measurable change.
    """

    return round(
        ablated_score - baseline_score,
        4,
    )


def classify_impact(
    score_delta: float,
    *,
    neutral_threshold: float = 1e-6,
) -> ImpactDirection:
    """
    Classify evaluator impact from the score delta.

    A tolerance avoids floating-point noise being interpreted
    as meaningful impact.
    """

    if score_delta > neutral_threshold:
        return "IMPROVEMENT"

    if score_delta < -neutral_threshold:
        return "REGRESSION"

    return "NEUTRAL"


def calculate_relative_impact(
    baseline_score: float,
    ablated_score: float,
) -> float:
    """
    Calculate relative percentage change.

    Returns a ratio rather than a percentage.

    Example:
        baseline = 0.8
        ablated  = 0.6

        result = -0.25

    Meaning:
        25% relative degradation.
    """

    if baseline_score == 0:
        return 0.0

    return round(
        (ablated_score - baseline_score)
        / baseline_score,
        4,
    )


def rank_ablation_results(
    results: Iterable[AblationCaseResult],
) -> list[AblationCaseResult]:
    """
    Rank completed ablation results by absolute evaluator impact.

    Failed and skipped experiments are excluded.

    Largest absolute score change comes first.
    """

    completed = [
        result
        for result in results
        if result.status == "COMPLETED"
        and result.score_delta is not None
    ]

    return sorted(
        completed,
        key=lambda result: abs(result.score_delta or 0.0),
        reverse=True,
    )


def most_impactful_evaluator(
    results: Iterable[AblationCaseResult],
) -> str | None:
    """
    Return the evaluator whose removal caused the largest
    absolute change in reliability.
    """

    ranked = rank_ablation_results(results)

    if not ranked:
        return None

    return ranked[0].evaluator_removed


def least_impactful_evaluator(
    results: Iterable[AblationCaseResult],
) -> str | None:
    """
    Return the evaluator whose removal caused the smallest
    absolute change.
    """

    completed = [
        result
        for result in results
        if result.status == "COMPLETED"
        and result.score_delta is not None
    ]

    if not completed:
        return None

    result = min(
        completed,
        key=lambda item: abs(item.score_delta or 0.0),
    )

    return result.evaluator_removed