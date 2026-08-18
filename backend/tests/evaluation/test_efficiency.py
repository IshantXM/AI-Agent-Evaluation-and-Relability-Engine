import json

import pytest

from backend.app.evaluation.core.models import AgentTrace
from backend.app.evaluation.evaluators.efficiency import (
    EfficiencyEvaluator,
)


def load_trace(filename: str) -> AgentTrace:
    with open(
        f"backend/tests/fixtures/{filename}",
        encoding="utf-8",
    ) as file:
        return AgentTrace.model_validate(json.load(file))


@pytest.mark.asyncio
async def test_efficient_trace_passes():
    trace = load_trace("efficient_trace.json")

    result = await EfficiencyEvaluator().evaluate(trace)

    assert result.evaluator == "efficiency"
    assert result.verdict == "PASS"
    assert result.score >= 0.90


@pytest.mark.asyncio
async def test_inefficient_trace_fails():
    trace = load_trace("inefficient_trace.json")

    result = await EfficiencyEvaluator().evaluate(trace)

    assert result.evaluator == "efficiency"
    assert result.verdict == "FAIL"
    assert result.score < 0.60


@pytest.mark.asyncio
async def test_efficiency_evidence_is_recorded():
    trace = load_trace("efficient_trace.json")

    result = await EfficiencyEvaluator().evaluate(trace)

    assert len(result.evidence) == 4

    evidence_types = {
        evidence.metadata.get("metric")
        for evidence in result.evidence
    }

    assert "latency_ms" in evidence_types
    assert "estimated_cost" in evidence_types
    assert "tokens" in evidence_types
    assert "calls" in evidence_types