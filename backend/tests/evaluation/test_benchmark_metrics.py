from backend.app.evaluation.benchmark.metrics import (
    BenchmarkMetrics,
)
from backend.app.evaluation.benchmark.models import (
    BenchmarkCaseResult,
    BenchmarkEvaluationResult,
)


def make_evaluation(
    *,
    evaluator: str = "correctness",
    passed: bool = True,
    score: float = 0.9,
    score_error: float | None = 0.1,
) -> BenchmarkEvaluationResult:
    return BenchmarkEvaluationResult(
        evaluator=evaluator,
        expected_verdict="PASS",
        actual_verdict="PASS" if passed else "FAIL",
        expected_score_min=0.8,
        expected_score_max=None,
        actual_score=score,
        passed=passed,
        score_error=score_error,
    )


def make_case(
    *,
    case_id: str,
    passed: bool,
    category: str,
    difficulty: str,
    evaluations: list[BenchmarkEvaluationResult],
) -> BenchmarkCaseResult:
    return BenchmarkCaseResult(
        case_id=case_id,
        run_id=f"run-{case_id}",
        passed=passed,
        evaluations=evaluations,
        metadata={
            "category": category,
            "difficulty": difficulty,
        },
    )


def test_metrics_summarize_empty_results() -> None:
    summary = BenchmarkMetrics.summarize([])

    assert summary.total_cases == 0
    assert summary.passed_cases == 0
    assert summary.failed_cases == 0
    assert summary.case_accuracy == 0.0

    assert summary.total_evaluations == 0
    assert summary.passed_evaluations == 0
    assert summary.evaluation_accuracy == 0.0

    assert summary.mean_score_error == 0.0
    assert summary.metadata["categories"] == {}
    assert summary.metadata["difficulties"] == {}


def test_metrics_calculate_case_accuracy() -> None:
    results = [
        make_case(
            case_id="case-1",
            passed=True,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation()
            ],
        ),
        make_case(
            case_id="case-2",
            passed=False,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation(
                    passed=False,
                    score=0.2,
                    score_error=0.2,
                )
            ],
        ),
    ]

    summary = BenchmarkMetrics.summarize(results)

    assert summary.total_cases == 2
    assert summary.passed_cases == 1
    assert summary.failed_cases == 1
    assert summary.case_accuracy == 0.5


def test_metrics_calculate_evaluation_accuracy() -> None:
    results = [
        make_case(
            case_id="case-1",
            passed=True,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation(passed=True)
            ],
        ),
        make_case(
            case_id="case-2",
            passed=False,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation(
                    passed=False,
                    score_error=0.2,
                )
            ],
        ),
    ]

    summary = BenchmarkMetrics.summarize(results)

    assert summary.total_evaluations == 2
    assert summary.passed_evaluations == 1
    assert summary.evaluation_accuracy == 0.5


def test_metrics_calculate_mean_score_error() -> None:
    results = [
        make_case(
            case_id="case-1",
            passed=True,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation(
                    score_error=0.10
                )
            ],
        ),
        make_case(
            case_id="case-2",
            passed=True,
            category="grounding",
            difficulty="medium",
            evaluations=[
                make_evaluation(
                    score_error=0.30
                )
            ],
        ),
    ]

    summary = BenchmarkMetrics.summarize(results)

    assert summary.mean_score_error == 0.2


def test_metrics_ignore_missing_score_error() -> None:
    results = [
        make_case(
            case_id="case-1",
            passed=False,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation(
                    passed=False,
                    score_error=None,
                )
            ],
        ),
        make_case(
            case_id="case-2",
            passed=True,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation(
                    score_error=0.2
                )
            ],
        ),
    ]

    summary = BenchmarkMetrics.summarize(results)

    assert summary.mean_score_error == 0.2


def test_metrics_build_category_breakdown() -> None:
    results = [
        make_case(
            case_id="case-1",
            passed=True,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation()
            ],
        ),
        make_case(
            case_id="case-2",
            passed=False,
            category="correctness",
            difficulty="medium",
            evaluations=[
                make_evaluation(passed=False)
            ],
        ),
        make_case(
            case_id="case-3",
            passed=True,
            category="safety",
            difficulty="hard",
            evaluations=[
                make_evaluation()
            ],
        ),
    ]

    summary = BenchmarkMetrics.summarize(results)

    assert summary.metadata["categories"] == {
        "correctness": {
            "total": 2,
            "passed": 1,
            "failed": 1,
            "accuracy": 0.5,
        },
        "safety": {
            "total": 1,
            "passed": 1,
            "failed": 0,
            "accuracy": 1.0,
        },
    }


def test_metrics_build_difficulty_breakdown() -> None:
    results = [
        make_case(
            case_id="case-1",
            passed=True,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation()
            ],
        ),
        make_case(
            case_id="case-2",
            passed=False,
            category="efficiency",
            difficulty="medium",
            evaluations=[
                make_evaluation(passed=False)
            ],
        ),
        make_case(
            case_id="case-3",
            passed=True,
            category="safety",
            difficulty="hard",
            evaluations=[
                make_evaluation()
            ],
        ),
    ]

    summary = BenchmarkMetrics.summarize(results)

    assert summary.metadata["difficulties"] == {
        "easy": {
            "total": 1,
            "passed": 1,
            "failed": 0,
            "accuracy": 1.0,
        },
        "hard": {
            "total": 1,
            "passed": 1,
            "failed": 0,
            "accuracy": 1.0,
        },
        "medium": {
            "total": 1,
            "passed": 0,
            "failed": 1,
            "accuracy": 0.0,
        },
    }


def test_metrics_accept_generator_input() -> None:
    results = (
        make_case(
            case_id=f"case-{index}",
            passed=True,
            category="correctness",
            difficulty="easy",
            evaluations=[
                make_evaluation()
            ],
        )
        for index in range(3)
    )

    summary = BenchmarkMetrics.summarize(results)

    assert summary.total_cases == 3
    assert summary.passed_cases == 3
    assert summary.case_accuracy == 1.0