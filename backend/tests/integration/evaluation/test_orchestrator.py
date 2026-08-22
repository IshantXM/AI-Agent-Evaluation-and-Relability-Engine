import json
from pathlib import Path

import pytest

from backend.app.evaluation.core.models import AgentTrace, EvaluationResult
from backend.app.evaluation.core.registry import EvaluatorRegistry
from backend.app.evaluation.evaluators.correctness import CorrectnessEvaluator
from backend.app.evaluation.evaluators.efficiency import EfficiencyEvaluator
from backend.app.evaluation.evaluators.grounding import GroundingEvaluator
from backend.app.evaluation.evaluators.safety import SafetyEvaluator
from backend.app.evaluation.evaluators.tool_use import ToolUseEvaluator
from backend.app.evaluation.orchestration import EvaluationOrchestrator


FIXTURES = Path("backend/tests/fixtures/traces")


def load_trace(filename: str) -> AgentTrace:
    with open(FIXTURES / filename, encoding="utf-8") as file:
        return AgentTrace.model_validate(json.load(file))


def build_registry() -> EvaluatorRegistry:
    registry = EvaluatorRegistry()

    registry.register(CorrectnessEvaluator())
    registry.register(EfficiencyEvaluator())
    registry.register(GroundingEvaluator())
    registry.register(SafetyEvaluator())
    registry.register(ToolUseEvaluator())

    return registry


@pytest.mark.asyncio
async def test_orchestrator_runs_all_evaluators():
    trace = load_trace("correct_trace.json")

    registry = build_registry()
    orchestrator = EvaluationOrchestrator(registry)

    results = await orchestrator.evaluate(trace)

    assert len(results) == 5

    assert [result.evaluator for result in results] == [
        "correctness",
        "efficiency",
        "grounding",
        "safety",
        "tool_use",
    ]


@pytest.mark.asyncio
async def test_orchestrator_runs_selected_evaluators():
    trace = load_trace("correct_trace.json")

    registry = build_registry()
    orchestrator = EvaluationOrchestrator(registry)

    results = await orchestrator.evaluate(
        trace,
        evaluators=["correctness", "safety"],
    )

    assert len(results) == 2

    assert [result.evaluator for result in results] == [
        "correctness",
        "safety",
    ]


@pytest.mark.asyncio
async def test_orchestrator_returns_standardized_results():
    trace = load_trace("correct_trace.json")

    registry = build_registry()
    orchestrator = EvaluationOrchestrator(registry)

    results = await orchestrator.evaluate(trace)

    for result in results:
        assert isinstance(result, EvaluationResult)
        assert result.run_id == trace.run_id
        assert 0 <= result.score <= 1
        assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_orchestrator_rejects_unknown_evaluator():
    trace = load_trace("correct_trace.json")

    registry = build_registry()
    orchestrator = EvaluationOrchestrator(registry)

    with pytest.raises(KeyError):
        await orchestrator.evaluate(
            trace,
            evaluators=["does_not_exist"],
        )