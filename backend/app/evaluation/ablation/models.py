from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AblationStatus = Literal[
    "COMPLETED",
    "FAILED",
    "SKIPPED",
]

ImpactDirection = Literal[
    "IMPROVEMENT",
    "REGRESSION",
    "NEUTRAL",
]


class AblationCase(BaseModel):
    """
    Immutable definition of a single leave-one-evaluator-out experiment.

    The experiment answers:

        "How does system reliability change when evaluator X
         is removed from the evaluation pipeline?"
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    run_id: str

    evaluator_to_remove: str

    baseline_score: float = Field(ge=0.0, le=1.0)

    baseline_evaluator_count: int = Field(ge=0)

    metadata: dict[str, Any] = Field(default_factory=dict)


class AblationCaseResult(BaseModel):
    """
    Operational result of one ablation experiment.
    """

    model_config = ConfigDict(extra="forbid")

    case_id: str
    run_id: str

    evaluator_removed: str

    status: AblationStatus

    baseline_score: float = Field(ge=0.0, le=1.0)

    ablated_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    score_delta: float | None = None

    impact_direction: ImpactDirection | None = None

    baseline_evaluator_count: int = Field(ge=0)

    ablated_evaluator_count: int | None = Field(
        default=None,
        ge=0,
    )

    evaluation_ids: list[str] = Field(default_factory=list)

    error: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class AblationReport(BaseModel):
    """
    Aggregated result of an evaluator ablation study.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str

    baseline_score: float = Field(ge=0.0, le=1.0)

    baseline_evaluator_count: int = Field(ge=0)

    results: list[AblationCaseResult] = Field(
        default_factory=list
    )

    most_impactful_evaluator: str | None = None

    least_impactful_evaluator: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )