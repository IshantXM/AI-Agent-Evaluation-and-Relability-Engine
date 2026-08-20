from __future__ import annotations

import pytest

from backend.app.evaluation.agents.critic import CriticAgent
from backend.app.evaluation.core.models import (
    AgentTrace,
    EvaluationResult,
)
from backend.app.evaluation.core.registry import EvaluatorRegistry
from backend.app.evaluation.orchestration.orchestrator import (
    EvaluationOrchestrator,
)
from backend.app.evaluation.orchestration.pipeline import (
    EvaluationPipeline,
)


class StubEvaluator:
    def __init__(
        self,
        name: str,
        result: EvaluationResult,
    ) -> None:
        self.name = name
        self._result = result

    async def evaluate(
        self,
        trace: AgentTrace,
    ) -> EvaluationResult:
        return self._result


def make_trace() -> AgentTrace:
    return AgentTrace(
        run_id="run-001",
        agent_id="agent-001",
        agent_version="1.0.0",
        task_id="task-001",
        task={
            "input": "Test task",
            "expected_output": "Expected answer",
        },
        events=[],
        metrics={
            "latency_ms": 10,
            "input_tokens": 10,
            "output_tokens": 20,
            "llm_calls": 1,
            "tool_calls": 0,
            "estimated_cost": 0.01,
        },
        final_output="Expected answer",
        status="success",
    )


def make_result(
    evaluator: str,
    score: float,
    verdict: str = "PASS",
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
        evidence=[],
        summary=f"{evaluator} evaluation",
    )


@pytest.mark.asyncio
async def test_pipeline_runs_orchestrator_and_critic():

    registry = EvaluatorRegistry()

    registry.register(
        StubEvaluator(
            "correctness",
            make_result(
                "correctness",
                0.95,
            ),
        )
    )

    registry.register(
        StubEvaluator(
            "grounding",
            make_result(
                "grounding",
                0.90,
            ),
        )
    )

    orchestrator = EvaluationOrchestrator(registry)

    pipeline = EvaluationPipeline(
        orchestrator=orchestrator,
        critic=CriticAgent(),
    )

    result = await pipeline.evaluate(
        make_trace()
    )

    assert result.run_id == "run-001"

    assert len(result.evaluations) == 2

    assert result.consensus.status == "CONSISTENT"

    assert result.score > 0.90

    assert result.confidence > 0.80


@pytest.mark.asyncio
async def test_pipeline_supports_selected_evaluators():

    registry = EvaluatorRegistry()

    registry.register(
        StubEvaluator(
            "correctness",
            make_result(
                "correctness",
                0.95,
            ),
        )
    )

    registry.register(
        StubEvaluator(
            "grounding",
            make_result(
                "grounding",
                0.90,
            ),
        )
    )

    registry.register(
        StubEvaluator(
            "efficiency",
            make_result(
                "efficiency",
                0.85,
            ),
        )
    )

    pipeline = EvaluationPipeline(
        orchestrator=EvaluationOrchestrator(registry)
    )

    result = await pipeline.evaluate(
        make_trace(),
        evaluators=[
            "correctness",
            "efficiency",
        ],
    )

    assert len(result.evaluations) == 2

    assert {
        evaluation.evaluator
        for evaluation in result.evaluations
    } == {
        "correctness",
        "efficiency",
    }


@pytest.mark.asyncio
async def test_pipeline_propagates_evaluator_failure_as_error():

    class BrokenEvaluator:
        name = "broken"

        async def evaluate(
            self,
            trace: AgentTrace,
        ) -> EvaluationResult:
            raise RuntimeError("simulated failure")

    registry = EvaluatorRegistry()

    registry.register(
        BrokenEvaluator()
    )

    pipeline = EvaluationPipeline(
        orchestrator=EvaluationOrchestrator(registry)
    )

    result = await pipeline.evaluate(
        make_trace()
    )

    assert len(result.evaluations) == 1

    evaluation = result.evaluations[0]

    assert evaluation.evaluator == "broken"
    assert evaluation.verdict == "ERROR"
    assert evaluation.metadata["orchestrator_error"] is True

    assert result.consensus.status == (
        "INSUFFICIENT_EVIDENCE"
    )


@pytest.mark.asyncio
async def test_pipeline_detects_cross_evaluator_conflict():

    registry = EvaluatorRegistry()

    registry.register(
        StubEvaluator(
            "correctness",
            make_result(
                "correctness",
                0.95,
                "PASS",
            ),
        )
    )

    registry.register(
        StubEvaluator(
            "grounding",
            make_result(
                "grounding",
                0.10,
                "FAIL",
            ),
        )
    )

    pipeline = EvaluationPipeline(
        orchestrator=EvaluationOrchestrator(registry)
    )

    result = await pipeline.evaluate(
        make_trace()
    )

    assert len(result.consensus.conflicts) >= 1

    assert result.consensus.status == (
        "MAJOR_CONFLICT"
    )

    assert result.consensus.confidence < 0.90


@pytest.mark.asyncio
async def test_pipeline_score_and_confidence_match_consensus():

    registry = EvaluatorRegistry()

    registry.register(
        StubEvaluator(
            "correctness",
            make_result(
                "correctness",
                0.80,
            ),
        )
    )

    registry.register(
        StubEvaluator(
            "grounding",
            make_result(
                "grounding",
                0.90,
            ),
        )
    )

    pipeline = EvaluationPipeline(
        orchestrator=EvaluationOrchestrator(registry)
    )

    result = await pipeline.evaluate(
        make_trace()
    )

    assert result.score == (
        result.consensus.consensus_score
    )

    assert result.confidence == (
        result.consensus.confidence
    )