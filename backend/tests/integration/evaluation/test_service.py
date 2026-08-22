from __future__ import annotations

import pytest

from backend.app.evaluation.core.models import (
    AgentTrace,
    TaskDefinition,
    TraceMetrics,
)
from backend.app.evaluation.core.registry import EvaluatorRegistry
from backend.app.evaluation.evaluators.correctness import (
    CorrectnessEvaluator,
)
from backend.app.evaluation.evaluators.grounding import (
    GroundingEvaluator,
)
from backend.app.evaluation.orchestration import (
    EvaluationOrchestrator,
    EvaluationService,
)


def make_trace() -> AgentTrace:
    return AgentTrace(
        run_id="run-service-001",
        agent_id="test-agent",
        agent_version="1.0.0",
        task_id="task-001",
        task=TaskDefinition(
            input="What is 2 + 2?",
            expected_output="4",
        ),
        events=[],
        metrics=TraceMetrics(),
        final_output="4",
        status="success",
    )


def make_service() -> EvaluationService:
    registry = EvaluatorRegistry()

    registry.register(CorrectnessEvaluator())
    registry.register(GroundingEvaluator())

    orchestrator = EvaluationOrchestrator(registry)

    return EvaluationService(
        orchestrator=orchestrator,
    )


@pytest.mark.asyncio
async def test_service_produces_evaluations_consensus_and_report():

    service = make_service()

    result = await service.evaluate(
        make_trace(),
    )

    assert result.run_id == "run-service-001"

    assert len(result.evaluations) == 2

    assert result.consensus.run_id == "run-service-001"

    assert result.report.run_id == "run-service-001"
    assert result.report.agent_id == "test-agent"
    assert result.report.agent_version == "1.0.0"


@pytest.mark.asyncio
async def test_service_report_contains_required_dimensions():

    service = make_service()

    result = await service.evaluate(
        make_trace(),
    )

    assert set(result.report.dimensions.keys()) == {
        "correctness",
        "grounding",
        "tool_use",
        "safety",
        "robustness",
        "efficiency",
    }


@pytest.mark.asyncio
async def test_service_preserves_consensus_separately_from_report():

    service = make_service()

    result = await service.evaluate(
        make_trace(),
    )

    assert result.consensus is not None

    report_data = result.report.model_dump()

    assert "consensus" not in report_data
    assert "consensus_score" not in report_data


@pytest.mark.asyncio
async def test_service_supports_selected_evaluators():

    service = make_service()

    result = await service.evaluate(
        make_trace(),
        evaluators=["correctness"],
    )

    assert len(result.evaluations) == 1
    assert result.evaluations[0].evaluator == "correctness"


@pytest.mark.asyncio
async def test_service_propagates_regression_context():

    service = make_service()

    result = await service.evaluate(
        make_trace(),
        previous_score=0.50,
        previous_version="0.9.0",
    )

    assert result.report.regression.previous_score == 0.50
    assert result.report.regression.previous_version == "0.9.0"
    assert result.report.regression.score_delta is not None