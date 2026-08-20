import json
from pathlib import Path

import pytest

from backend.app.evaluation.core.models import AgentTrace
from backend.app.evaluation.core.registry import EvaluatorRegistry
from backend.app.evaluation.evaluators.correctness import CorrectnessEvaluator
from backend.app.evaluation.evaluators.efficiency import EfficiencyEvaluator
from backend.app.evaluation.evaluators.grounding import GroundingEvaluator
from backend.app.evaluation.evaluators.safety import SafetyEvaluator
from backend.app.evaluation.evaluators.tool_use import ToolUseEvaluator
from backend.app.evaluation.orchestration import (
    EvaluationOrchestrator,
    ReportBuilder,
)


FIXTURES = Path("backend/tests/fixtures")


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
async def test_report_contains_all_dimensions():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(build_registry())

    results = await orchestrator.evaluate(trace)

    report = ReportBuilder().build(
        run_id=trace.run_id,
        agent_id=trace.agent_id,
        agent_version=trace.agent_version,
        results=results,
    )

    assert set(report.dimensions.keys()) == {
        "correctness",
        "grounding",
        "tool_use",
        "safety",
        "robustness",
        "efficiency",
    }


@pytest.mark.asyncio
async def test_unevaluated_dimension_is_not_marked_failed():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(build_registry())

    results = await orchestrator.evaluate(trace)

    report = ReportBuilder().build(
        run_id=trace.run_id,
        agent_id=trace.agent_id,
        agent_version=trace.agent_version,
        results=results,
    )

    robustness = report.dimensions["robustness"]

    assert robustness.status == "NOT_EVALUATED"
    assert robustness.score == 0.0
    assert robustness.confidence == 0.0


@pytest.mark.asyncio
async def test_failures_are_propagated_to_report():
    trace = load_trace("incorrect_trace.json")

    orchestrator = EvaluationOrchestrator(build_registry())

    results = await orchestrator.evaluate(trace)

    report = ReportBuilder().build(
        run_id=trace.run_id,
        agent_id=trace.agent_id,
        agent_version=trace.agent_version,
        results=results,
    )

    assert len(report.failures) >= 1

    assert any(
        failure.evaluator == "correctness"
        for failure in report.failures
    )


@pytest.mark.asyncio
async def test_baseline_regression_is_created():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(build_registry())

    results = await orchestrator.evaluate(trace)

    report = ReportBuilder().build(
        run_id=trace.run_id,
        agent_id=trace.agent_id,
        agent_version=trace.agent_version,
        results=results,
    )

    assert report.regression.status == "BASELINE"
    assert report.regression.previous_score is None


@pytest.mark.asyncio
async def test_regression_is_detected():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(build_registry())

    results = await orchestrator.evaluate(trace)

    report = ReportBuilder().build(
        run_id=trace.run_id,
        agent_id=trace.agent_id,
        agent_version=trace.agent_version,
        results=results,
        previous_score=1.0,
        previous_version="0.9.0",
    )

    assert report.regression.status == "REGRESSED"
    assert report.regression.previous_version == "0.9.0"
    assert report.regression.score_delta < 0