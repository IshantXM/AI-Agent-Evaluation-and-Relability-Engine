from __future__ import annotations

from backend.app.evaluation.attribution import AttributionEngine
from backend.app.evaluation.core.models import (
    EvaluationResult,
    Evidence,
    Finding,
)


def make_result(
    *,
    evaluator: str,
    verdict: str,
    score: float = 0.3,
    confidence: float = 0.9,
    evaluation_id: str = "eval-1",
) -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=evaluation_id,
        run_id="run-123",
        evaluator=evaluator,
        verdict=verdict,
        score=score,
        confidence=confidence,
        summary=f"{evaluator} evaluation result",
    )


def test_attribution_ignores_successful_evaluations() -> None:
    engine = AttributionEngine()

    result = engine.attribute(
        run_id="run-123",
        evaluations=[
            make_result(
                evaluator="correctness",
                verdict="PASS",
                score=0.95,
            )
        ],
    )

    assert result.run_id == "run-123"
    assert result.attributions == []
    assert result.metadata["evaluations_processed"] == 1
    assert result.metadata["failures_attributed"] == 0


def test_attribution_maps_correctness_failure() -> None:
    engine = AttributionEngine()

    result = engine.attribute(
        run_id="run-123",
        evaluations=[
            make_result(
                evaluator="correctness",
                verdict="FAIL",
            )
        ],
    )

    assert len(result.attributions) == 1

    attribution = result.attributions[0]

    assert attribution.evaluator == "correctness"
    assert attribution.failure_type == "CORRECTNESS_FAILURE"
    assert attribution.cause == "GENERATION_FAILURE"
    assert attribution.stage == "GENERATION"
    assert attribution.confidence == 0.85


def test_attribution_maps_grounding_failure_to_retrieval() -> None:
    engine = AttributionEngine()

    result = engine.attribute(
        run_id="run-123",
        evaluations=[
            make_result(
                evaluator="grounding",
                verdict="FAIL",
            )
        ],
    )

    attribution = result.attributions[0]

    assert attribution.failure_type == "GROUNDING_FAILURE"
    assert attribution.cause == "RETRIEVAL_FAILURE"
    assert attribution.stage == "RETRIEVAL"


def test_attribution_maps_tool_failure() -> None:
    engine = AttributionEngine()

    result = engine.attribute(
        run_id="run-123",
        evaluations=[
            make_result(
                evaluator="tool_use",
                verdict="FAIL",
            )
        ],
    )

    attribution = result.attributions[0]

    assert attribution.failure_type == "TOOL_USE_FAILURE"
    assert attribution.cause == "TOOL_FAILURE"
    assert attribution.stage == "TOOL_EXECUTION"


def test_attribution_preserves_evaluator_evidence() -> None:
    engine = AttributionEngine()

    evaluation = make_result(
        evaluator="grounding",
        verdict="FAIL",
    )

    evaluation = evaluation.model_copy(
        update={
            "evidence": [
                Evidence(
                    evidence_id="evidence-1",
                    type="retrieval",
                    content="Retrieved context did not support claim.",
                    source="retriever",
                    metadata={
                        "document_count": 1,
                    },
                )
            ],
            "findings": [
                Finding(
                    finding_id="finding-1",
                    description="Unsupported claim detected.",
                    severity="high",
                )
            ],
        }
    )

    result = engine.attribute(
        run_id="run-123",
        evaluations=[evaluation],
    )

    attribution = result.attributions[0]

    assert len(attribution.evidence) == 2

    original_evidence = attribution.evidence[1]

    assert original_evidence.evaluator == "grounding"
    assert original_evidence.failure_type == "GROUNDING_FAILURE"
    assert original_evidence.value == (
        "Retrieved context did not support claim."
    )
    assert original_evidence.metadata["evidence_id"] == "evidence-1"


def test_attribution_preserves_evaluation_identity() -> None:
    engine = AttributionEngine()

    result = engine.attribute(
        run_id="run-123",
        evaluations=[
            make_result(
                evaluator="safety",
                verdict="FAIL",
                evaluation_id="evaluation-42",
            )
        ],
    )

    attribution = result.attributions[0]

    assert attribution.metadata["source_evaluation_id"] == (
        "evaluation-42"
    )


def test_unknown_failed_evaluator_is_not_speculatively_attributed() -> None:
    engine = AttributionEngine()

    result = engine.attribute(
        run_id="run-123",
        evaluations=[
            make_result(
                evaluator="unknown_evaluator",
                verdict="FAIL",
            )
        ],
    )

    assert result.attributions == []
    assert result.metadata["failures_attributed"] == 0
    assert result.metadata["unattributed_failures"] == 1


def test_multiple_failures_are_attributed_independently() -> None:
    engine = AttributionEngine()

    result = engine.attribute(
        run_id="run-123",
        evaluations=[
            make_result(
                evaluator="correctness",
                verdict="FAIL",
            ),
            make_result(
                evaluator="grounding",
                verdict="FAIL",
                evaluation_id="eval-2",
            ),
            make_result(
                evaluator="safety",
                verdict="PASS",
                score=1.0,
                evaluation_id="eval-3",
            ),
            make_result(
                evaluator="tool_use",
                verdict="FAIL",
                evaluation_id="eval-4",
            ),
        ],
    )

    assert len(result.attributions) == 3

    assert [
        attribution.evaluator
        for attribution in result.attributions
    ] == [
        "correctness",
        "grounding",
        "tool_use",
    ]

    assert result.metadata["evaluations_processed"] == 4
    assert result.metadata["failures_attributed"] == 3


def test_attribution_is_deterministic() -> None:
    engine = AttributionEngine()

    evaluations = [
        make_result(
            evaluator="correctness",
            verdict="FAIL",
        ),
        make_result(
            evaluator="grounding",
            verdict="FAIL",
            evaluation_id="eval-2",
        ),
    ]

    first = engine.attribute(
        run_id="run-123",
        evaluations=evaluations,
    )

    second = engine.attribute(
        run_id="run-123",
        evaluations=evaluations,
    )

    assert first == second