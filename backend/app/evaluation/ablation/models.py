from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    relative_impact: float | None = None

    impact_direction: ImpactDirection | None = None

    baseline_evaluator_count: int = Field(ge=0)

    ablated_evaluator_count: int | None = Field(
        default=None,
        ge=0,
    )

    evaluation_ids: list[str] = Field(default_factory=list)

    trial_results: list["AblationTrialResult"] = Field(
        default_factory=list
    )

    trial_count: int = Field(default=1, ge=1)
    mean_score: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_deviation: float | None = Field(default=None, ge=0.0)
    minimum_score: float | None = Field(default=None, ge=0.0, le=1.0)
    maximum_score: float | None = Field(default=None, ge=0.0, le=1.0)

    error: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_status_fields(self) -> "AblationCaseResult":
        if self.status == "COMPLETED" and (
            self.ablated_score is None
            or self.score_delta is None
            or "relative_impact" not in self.model_fields_set
            or self.impact_direction is None
        ):
            raise ValueError(
                "COMPLETED ablation results require scores, impacts, "
                "and impact direction."
            )

        if self.status == "FAILED" and (
            self.ablated_score is not None
            or self.score_delta is not None
            or self.relative_impact is not None
            or self.impact_direction is not None
            or not self.error
        ):
            raise ValueError(
                "FAILED ablation results require an error and no "
                "completed-result fields."
            )

        return self


class AblationTrialResult(BaseModel):
    """Result of one execution of an ablation case."""

    model_config = ConfigDict(extra="forbid")

    trial: int = Field(ge=1)
    status: AblationStatus
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    evaluation_ids: list[str] = Field(default_factory=list)
    error: str | None = None

    @model_validator(mode="after")
    def validate_trial_fields(self) -> "AblationTrialResult":
        if self.status == "COMPLETED" and self.score is None:
            raise ValueError("COMPLETED trials require a score.")
        if self.status == "FAILED" and (self.score is not None or not self.error):
            raise ValueError(
                "FAILED trials require an error and no score."
            )
        return self

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