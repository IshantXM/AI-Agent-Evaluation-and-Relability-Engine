from backend.app.evaluation.ablation.metrics import (
    calculate_relative_impact,
    calculate_score_delta,
    classify_impact,
    least_impactful_evaluator,
    most_impactful_evaluator,
    rank_ablation_results,
)
from backend.app.evaluation.ablation.models import (
    AblationCaseResult,
)


def make_result(
    evaluator: str,
    delta: float,
) -> AblationCaseResult:
    return AblationCaseResult(
        case_id=f"case-{evaluator}",
        run_id="run-001",
        evaluator_removed=evaluator,
        status="COMPLETED",
        baseline_score=0.8,
        ablated_score=0.8 + delta,
        score_delta=delta,
        impact_direction=classify_impact(delta),
        baseline_evaluator_count=5,
        ablated_evaluator_count=4,
    )


def test_score_delta_is_calculated():
    assert calculate_score_delta(
        0.8,
        0.6,
    ) == -0.2


def test_positive_delta_is_improvement():
    assert classify_impact(0.1) == "IMPROVEMENT"


def test_negative_delta_is_regression():
    assert classify_impact(-0.1) == "REGRESSION"


def test_small_delta_is_neutral():
    assert classify_impact(1e-7) == "NEUTRAL"


def test_relative_impact_is_calculated():
    assert calculate_relative_impact(
        0.8,
        0.6,
    ) == -0.25


def test_relative_impact_handles_zero_baseline():
    assert calculate_relative_impact(
        0.0,
        0.5,
    ) == 0.0


def test_results_are_ranked_by_absolute_impact():
    results = [
        make_result("correctness", -0.1),
        make_result("grounding", -0.3),
        make_result("safety", 0.05),
    ]

    ranked = rank_ablation_results(results)

    assert [
        result.evaluator_removed
        for result in ranked
    ] == [
        "grounding",
        "correctness",
        "safety",
    ]


def test_most_impactful_evaluator():
    results = [
        make_result("correctness", -0.1),
        make_result("grounding", -0.3),
    ]

    assert most_impactful_evaluator(results) == "grounding"


def test_least_impactful_evaluator():
    results = [
        make_result("correctness", -0.1),
        make_result("grounding", -0.3),
        make_result("safety", 0.01),
    ]

    assert least_impactful_evaluator(results) == "safety"


def test_failed_results_are_excluded_from_ranking():
    failed = AblationCaseResult(
        case_id="case-failed",
        run_id="run-001",
        evaluator_removed="safety",
        status="FAILED",
        baseline_score=0.8,
        baseline_evaluator_count=5,
        error="Evaluator crashed",
    )

    ranked = rank_ablation_results([failed])

    assert ranked == []
    assert most_impactful_evaluator([failed]) is None
    assert least_impactful_evaluator([failed]) is None