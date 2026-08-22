from __future__ import annotations

import pytest

from backend.app.evaluation.judges.critic import CriticAgent
from backend.app.evaluation.core.models import (
    EvaluationResult,
    Evidence,
)


def make_result(
    *,
    evaluator: str,
    verdict: str,
    score: float,
    confidence: float = 0.90,
) -> EvaluationResult:

    return EvaluationResult(
        evaluation_id=f"eval-{evaluator}",
        run_id="run-001",
        evaluator=evaluator,
        verdict=verdict,
        score=score,
        confidence=confidence,
        findings=[],
        evidence=[
            Evidence(
                evidence_id=f"evidence-{evaluator}",
                type="metric",
                content=f"{evaluator} evidence",
                metadata={},
            )
        ],
        summary=f"{evaluator} result",
    )


@pytest.mark.asyncio
async def test_consistent_evaluators_produce_consensus():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=0.95,
        ),
        make_result(
            evaluator="grounding",
            verdict="PASS",
            score=0.92,
        ),
        make_result(
            evaluator="safety",
            verdict="PASS",
            score=0.98,
        ),
    ]

    result = CriticAgent().evaluate(results)

    assert result.status == "CONSISTENT"
    assert result.consensus_score > 0.90
    assert result.confidence > 0.80
    assert len(result.conflicts) == 0


@pytest.mark.asyncio
async def test_pass_fail_conflict_is_detected():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=0.95,
        ),
        make_result(
            evaluator="grounding",
            verdict="FAIL",
            score=0.20,
        ),
    ]

    result = CriticAgent().evaluate(results)

    assert result.status == "MAJOR_CONFLICT"
    assert len(result.conflicts) >= 1

    conflict = result.conflicts[0]

    assert {
        "correctness",
        "grounding",
    }.issubset(set(conflict.evaluators))


@pytest.mark.asyncio
async def test_large_score_difference_is_detected():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=0.95,
        ),
        make_result(
            evaluator="efficiency",
            verdict="PARTIAL",
            score=0.30,
        ),
    ]

    result = CriticAgent().evaluate(results)

    assert len(result.conflicts) == 1
    assert result.conflicts[0].score_delta == 0.65


@pytest.mark.asyncio
async def test_small_score_difference_is_consistent():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=0.91,
        ),
        make_result(
            evaluator="grounding",
            verdict="PASS",
            score=0.89,
        ),
    ]

    result = CriticAgent().evaluate(results)

    assert result.status == "CONSISTENT"
    assert result.conflicts == []


@pytest.mark.asyncio
async def test_consensus_is_confidence_weighted():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=1.0,
            confidence=1.0,
        ),
        make_result(
            evaluator="grounding",
            verdict="FAIL",
            score=0.0,
            confidence=0.1,
        ),
    ]

    result = CriticAgent().evaluate(results)

    assert result.consensus_score > 0.85


@pytest.mark.asyncio
async def test_conflict_reduces_confidence():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=1.0,
            confidence=0.95,
        ),
        make_result(
            evaluator="grounding",
            verdict="FAIL",
            score=0.10,
            confidence=0.95,
        ),
    ]

    result = CriticAgent().evaluate(results)

    assert result.confidence < 0.95


@pytest.mark.asyncio
async def test_empty_results_are_insufficient():

    result = CriticAgent().evaluate([])

    assert result.status == "INSUFFICIENT_EVIDENCE"
    assert result.consensus_score == 0.0
    assert result.confidence == 0.0
    assert result.assessments == []


@pytest.mark.asyncio
async def test_assessments_preserve_evaluator_results():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=0.95,
        ),
        make_result(
            evaluator="safety",
            verdict="PASS",
            score=0.99,
        ),
    ]

    result = CriticAgent().evaluate(results)

    assert len(result.assessments) == 2

    assert result.assessments[0].evaluator == "correctness"
    assert result.assessments[0].evaluation_id == (
        "eval-correctness"
    )

    assert result.assessments[1].evaluator == "safety"


@pytest.mark.asyncio
async def test_evidence_is_linked_to_conflicts():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=0.95,
        ),
        make_result(
            evaluator="grounding",
            verdict="FAIL",
            score=0.20,
        ),
    ]

    result = CriticAgent().evaluate(results)

    conflict = result.conflicts[0]

    assert "evidence-correctness" in conflict.evidence_ids
    assert "evidence-grounding" in conflict.evidence_ids


@pytest.mark.asyncio
async def test_consensus_score_is_bounded():

    results = [
        make_result(
            evaluator="correctness",
            verdict="PASS",
            score=1.0,
        ),
        make_result(
            evaluator="grounding",
            verdict="FAIL",
            score=0.0,
        ),
    ]

    result = CriticAgent().evaluate(results)

    assert 0.0 <= result.consensus_score <= 1.0
    assert 0.0 <= result.confidence <= 1.0