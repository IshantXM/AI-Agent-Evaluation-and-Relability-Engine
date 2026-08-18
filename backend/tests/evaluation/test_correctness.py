import json
from pathlib import Path

import pytest

from backend.app.evaluation.core.models import AgentTrace
from backend.app.evaluation.evaluators.correctness import CorrectnessEvaluator


FIXTURES = Path(__file__).parent.parent / "fixtures"


def load_trace(filename: str) -> AgentTrace:
    with open(FIXTURES / filename, "r", encoding="utf-8") as file:
        return AgentTrace.model_validate(json.load(file))


@pytest.mark.asyncio
async def test_correct_trace_passes():
    trace = load_trace("correct_trace.json")

    result = await CorrectnessEvaluator().evaluate(trace)

    assert result.verdict == "PASS"
    assert result.score == 1.0
    assert result.confidence > 0.9
    assert len(result.findings) == 0


@pytest.mark.asyncio
async def test_incorrect_trace_fails():
    trace = load_trace("incorrect_trace.json")

    result = await CorrectnessEvaluator().evaluate(trace)

    assert result.verdict == "FAIL"
    assert result.score == 0.0
    assert len(result.findings) > 0