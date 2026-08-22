import json

import pytest

from backend.app.evaluation.core.models import AgentTrace
from backend.app.evaluation.evaluators.grounding import GroundingEvaluator


def load_trace(filename: str) -> AgentTrace:
    with open(
        f"backend/tests/fixtures/traces/{filename}",
        encoding="utf-8",
    ) as file:
        return AgentTrace.model_validate(json.load(file))


@pytest.mark.asyncio
async def test_grounded_trace_passes():
    trace = load_trace("grounded_trace.json")

    result = await GroundingEvaluator().evaluate(trace)

    assert result.evaluator == "grounding"
    assert result.verdict == "PASS"
    assert result.score == 1.0
    assert len(result.findings) == 0


@pytest.mark.asyncio
async def test_ungrounded_trace_fails():
    trace = load_trace("ungrounded_trace.json")

    result = await GroundingEvaluator().evaluate(trace)

    assert result.evaluator == "grounding"
    assert result.verdict == "FAIL"
    assert result.score == 0.0
    assert len(result.findings) == 1
    assert result.findings[0].severity == "high"


@pytest.mark.asyncio
async def test_grounding_evidence_is_recorded():
    trace = load_trace("grounded_trace.json")

    result = await GroundingEvaluator().evaluate(trace)

    assert len(result.evidence) >= 1

    retrieval_evidence = [
        item
        for item in result.evidence
        if item.type == "retrieval"
    ]

    assert len(retrieval_evidence) == 1
    assert (
        retrieval_evidence[0].metadata["grounding_status"]
        == "SUPPORTED"
    )


@pytest.mark.asyncio
async def test_unsupported_claim_is_recorded():
    trace = load_trace("ungrounded_trace.json")

    result = await GroundingEvaluator().evaluate(trace)

    unsupported = [
        item
        for item in result.evidence
        if item.metadata.get("grounding_status") == "UNSUPPORTED"
    ]

    assert len(unsupported) == 1
    assert "90 days" in unsupported[0].content