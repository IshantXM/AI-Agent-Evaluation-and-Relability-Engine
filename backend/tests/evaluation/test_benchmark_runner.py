from pathlib import Path

import pytest

from backend.app.evaluation.benchmark.corpus import BenchmarkCorpus
from backend.app.evaluation.benchmark.runner import BenchmarkRunner
from backend.app.evaluation.core.registry import EvaluatorRegistry
from backend.app.evaluation.evaluators.correctness import CorrectnessEvaluator
from backend.app.evaluation.evaluators.efficiency import EfficiencyEvaluator
from backend.app.evaluation.evaluators.grounding import GroundingEvaluator
from backend.app.evaluation.evaluators.safety import SafetyEvaluator
from backend.app.evaluation.evaluators.tool_use import ToolUseEvaluator
from backend.app.evaluation.orchestration.orchestrator import (
    EvaluationOrchestrator,
)
from backend.app.evaluation.orchestration.pipeline import EvaluationPipeline


ROOT = Path(__file__).parents[2]

BENCHMARK_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "benchmark"
    / "benchmark_cases.json"
)

TRACE_DIRECTORY = ROOT / "tests" / "fixtures"


def build_registry() -> EvaluatorRegistry:
    """Build the canonical evaluator registry used by the benchmark."""

    registry = EvaluatorRegistry()

    for evaluator in (
        CorrectnessEvaluator(),
        EfficiencyEvaluator(),
        GroundingEvaluator(),
        SafetyEvaluator(),
        ToolUseEvaluator(),
    ):
        registry.register(evaluator)

    return registry


def build_runner() -> BenchmarkRunner:
    """Build a benchmark runner using the production evaluation pipeline."""

    orchestrator = EvaluationOrchestrator(
        build_registry()
    )

    pipeline = EvaluationPipeline(
        orchestrator=orchestrator,
    )

    return BenchmarkRunner(
        pipeline=pipeline,
        trace_directory=TRACE_DIRECTORY,
    )


@pytest.mark.asyncio
async def test_runner_executes_single_case() -> None:
    corpus = BenchmarkCorpus.from_file(
        BENCHMARK_PATH
    )

    result = await build_runner().run_case(
        corpus.get("correctness_correct")
    )

    assert result.case_id == "correctness_correct"
    assert result.run_id
    assert result.evaluations
    assert result.passed is True


@pytest.mark.asyncio
async def test_runner_executes_selected_cases() -> None:
    corpus = BenchmarkCorpus.from_file(
        BENCHMARK_PATH
    )

    case_ids = [
        "correctness_correct",
        "correctness_incorrect",
    ]

    results = await build_runner().run(
        corpus,
        case_ids,
    )

    assert len(results) == len(case_ids)
    assert [result.case_id for result in results] == case_ids


@pytest.mark.asyncio
async def test_runner_executes_entire_corpus() -> None:
    corpus = BenchmarkCorpus.from_file(
        BENCHMARK_PATH
    )

    results = await build_runner().run(corpus)

    assert len(results) == len(corpus)


@pytest.mark.asyncio
async def test_runner_detects_missing_evaluator() -> None:
    corpus = BenchmarkCorpus.from_file(
        BENCHMARK_PATH
    )

    case = corpus.get(
        "correctness_correct"
    ).model_copy(
        update={
            "expected_evaluations": {
                "nonexistent_evaluator": {
                    "verdict": "PASS",
                }
            }
        }
    )

    result = await build_runner().run_case(case)

    assert result.passed is False
    assert result.evaluations[0].actual_verdict == "MISSING"


@pytest.mark.asyncio
async def test_runner_fails_for_missing_trace() -> None:
    corpus = BenchmarkCorpus.from_file(
        BENCHMARK_PATH
    )

    case = corpus.get(
        "correctness_correct"
    ).model_copy(
        update={
            "trace_file": "does_not_exist.json"
        }
    )

    with pytest.raises(FileNotFoundError):
        await build_runner().run_case(case)