import json
from pathlib import Path

import pytest

from backend.app.evaluation.ablation import AblationRunner
from backend.app.evaluation.core.models import AgentTrace
from backend.app.evaluation.core.registry import EvaluatorRegistry
from backend.app.evaluation.evaluators.correctness import (
    CorrectnessEvaluator,
)
from backend.app.evaluation.evaluators.efficiency import (
    EfficiencyEvaluator,
)
from backend.app.evaluation.evaluators.grounding import (
    GroundingEvaluator,
)
from backend.app.evaluation.evaluators.safety import (
    SafetyEvaluator,
)
from backend.app.evaluation.evaluators.tool_use import (
    ToolUseEvaluator,
)
from backend.app.evaluation.orchestration import (
    EvaluationOrchestrator,
)


FIXTURES = Path("backend/tests/fixtures")


def load_trace(filename: str) -> AgentTrace:
    with open(
        FIXTURES / filename,
        encoding="utf-8",
    ) as file:
        return AgentTrace.model_validate(
            json.load(file)
        )


def build_registry() -> EvaluatorRegistry:
    registry = EvaluatorRegistry()

    registry.register(CorrectnessEvaluator())
    registry.register(EfficiencyEvaluator())
    registry.register(GroundingEvaluator())
    registry.register(SafetyEvaluator())
    registry.register(ToolUseEvaluator())

    return registry


@pytest.mark.asyncio
async def test_ablation_runs_one_case_per_evaluator():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    runner = AblationRunner(orchestrator)

    report = await runner.run(trace)

    assert len(report.results) == 5

    assert {
        result.evaluator_removed
        for result in report.results
    } == {
        "correctness",
        "efficiency",
        "grounding",
        "safety",
        "tool_use",
    }


@pytest.mark.asyncio
async def test_ablation_removes_exactly_one_evaluator():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    runner = AblationRunner(orchestrator)

    report = await runner.run(trace)

    for result in report.results:
        remaining = result.metadata[
            "remaining_evaluators"
        ]

        assert result.evaluator_removed not in remaining
        assert len(remaining) == 4


@pytest.mark.asyncio
async def test_ablation_results_are_completed():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    runner = AblationRunner(orchestrator)

    report = await runner.run(trace)

    assert all(
        result.status == "COMPLETED"
        for result in report.results
    )


@pytest.mark.asyncio
async def test_ablation_scores_are_bounded():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    runner = AblationRunner(orchestrator)

    report = await runner.run(trace)

    for result in report.results:
        assert result.ablated_score is not None
        assert 0.0 <= result.ablated_score <= 1.0

        assert result.score_delta is not None


@pytest.mark.asyncio
async def test_ablation_report_identifies_impact():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    runner = AblationRunner(orchestrator)

    report = await runner.run(trace)

    assert report.baseline_score >= 0.0
    assert report.baseline_score <= 1.0

    completed = [
        result
        for result in report.results
        if result.status == "COMPLETED"
    ]

    assert completed


@pytest.mark.asyncio
async def test_selected_evaluators_can_be_ablated():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    runner = AblationRunner(orchestrator)

    report = await runner.run(
        trace,
        evaluators=[
            "correctness",
            "grounding",
        ],
    )

    assert len(report.results) == 2

    assert {
        result.evaluator_removed
        for result in report.results
    } == {
        "correctness",
        "grounding",
    }


@pytest.mark.asyncio
async def test_sequential_and_parallel_execution_match():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    runner = AblationRunner(orchestrator)

    parallel_report = await runner.run(
        trace,
        parallel=True,
    )

    sequential_report = await runner.run(
        trace,
        parallel=False,
    )

    parallel_scores = {
        result.evaluator_removed: result.ablated_score
        for result in parallel_report.results
    }

    sequential_scores = {
        result.evaluator_removed: result.ablated_score
        for result in sequential_report.results
    }

    assert parallel_scores == sequential_scores