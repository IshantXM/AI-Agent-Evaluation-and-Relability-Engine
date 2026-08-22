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


class FailingAblationOrchestrator(EvaluationOrchestrator):
    def __init__(self, registry: EvaluatorRegistry) -> None:
        super().__init__(registry)
        self.calls = 0

    async def evaluate(self, trace, evaluators=None):
        self.calls += 1
        if self.calls > 1:
            raise ValueError("deliberate ablation failure")
        return await super().evaluate(trace, evaluators=evaluators)


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
        if result.ablated_score is not None
    )
    assert any(result.status == "FAILED" for result in report.results)


@pytest.mark.asyncio
async def test_ablation_scores_are_bounded():
    trace = load_trace("correct_trace.json")

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    runner = AblationRunner(orchestrator)

    report = await runner.run(trace)

    for result in report.results:
        if result.status == "FAILED":
            assert result.ablated_score is None
            continue
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


@pytest.mark.asyncio
async def test_ablation_execution_failure_is_failed_result():
    trace = load_trace("correct_trace.json")
    runner = AblationRunner(
        FailingAblationOrchestrator(build_registry())
    )

    report = await runner.run(trace, evaluators=["safety"])
    result = report.results[0]

    assert result.status == "FAILED"
    assert result.ablated_score is None
    assert result.score_delta is None
    assert result.relative_impact is None
    assert "ValueError" in (result.error or "")


@pytest.mark.asyncio
async def test_duplicate_evaluator_is_rejected_before_baseline():
    trace = load_trace("correct_trace.json")
    runner = AblationRunner(EvaluationOrchestrator(build_registry()))

    with pytest.raises(ValueError, match="unique"):
        await runner.run(trace, evaluators=["safety", "safety"])


@pytest.mark.asyncio
async def test_unknown_evaluator_is_rejected_before_baseline():
    trace = load_trace("correct_trace.json")
    runner = AblationRunner(EvaluationOrchestrator(build_registry()))

    with pytest.raises(ValueError, match="Unknown"):
        await runner.run(trace, evaluators=["does_not_exist"])


@pytest.mark.asyncio
async def test_repeated_trials_store_summary_statistics():
    trace = load_trace("correct_trace.json")
    runner = AblationRunner(EvaluationOrchestrator(build_registry()))

    report = await runner.run(
        trace,
        evaluators=["correctness", "safety"],
        trials=3,
    )
    result = report.results[0]

    assert result.status == "COMPLETED"
    assert result.trial_count == 3
    assert len(result.trial_results) == 3
    assert result.mean_score == result.ablated_score
    assert result.standard_deviation == 0.0
    assert result.minimum_score == result.maximum_score