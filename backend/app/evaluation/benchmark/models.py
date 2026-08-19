from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


BenchmarkDifficulty = Literal[
    "easy",
    "medium",
    "hard",
]

BenchmarkExpectation = Literal[
    "PASS",
    "FAIL",
]


class EvaluationExpectation(BaseModel):
    """
    Expected outcome for a single evaluator.

    The benchmark deliberately stores ground truth separately
    from the evaluator implementation.
    """

    model_config = ConfigDict(extra="forbid")

    verdict: BenchmarkExpectation

    min_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    max_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )


class BenchmarkCase(BaseModel):
    """
    Ground-truth definition for one benchmark scenario.

    A benchmark case points to an existing AgentTrace fixture
    rather than embedding the trace itself.
    """

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)

    name: str = Field(min_length=1)

    trace_file: str = Field(min_length=1)

    category: str = Field(min_length=1)

    difficulty: BenchmarkDifficulty

    expected_evaluations: dict[
        str,
        EvaluationExpectation,
    ] = Field(
        default_factory=dict,
    )

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )


class BenchmarkEvaluationResult(BaseModel):
    """
    Result of comparing one evaluator's actual output
    against benchmark ground truth.
    """

    model_config = ConfigDict(extra="forbid")

    evaluator: str

    expected_verdict: BenchmarkExpectation

    actual_verdict: str

    expected_score_min: float | None = None

    expected_score_max: float | None = None

    actual_score: float = Field(
        ge=0,
        le=1,
    )

    passed: bool

    score_error: float | None = None

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )


class BenchmarkCaseResult(BaseModel):
    """
    Complete result for a single benchmark case.
    """

    model_config = ConfigDict(extra="forbid")

    case_id: str

    run_id: str

    passed: bool

    evaluations: list[BenchmarkEvaluationResult] = Field(
        default_factory=list,
    )

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )


class BenchmarkSummary(BaseModel):
    """
    Aggregate benchmark outcome.

    This is intentionally independent from the final
    reliability report representation.
    """

    model_config = ConfigDict(extra="forbid")

    total_cases: int = Field(
        ge=0,
    )

    passed_cases: int = Field(
        ge=0,
    )

    failed_cases: int = Field(
        ge=0,
    )

    case_accuracy: float = Field(
        ge=0,
        le=1,
    )

    total_evaluations: int = Field(
        ge=0,
    )

    passed_evaluations: int = Field(
        ge=0,
    )

    evaluation_accuracy: float = Field(
        ge=0,
        le=1,
    )

    mean_score_error: float = Field(
        ge=0,
    )

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )