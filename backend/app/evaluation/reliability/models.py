from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ReliabilityStatus = Literal[
    "RELIABLE",
    "DEGRADED",
    "UNRELIABLE",
    "INSUFFICIENT_EVIDENCE",
]


RiskLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class ReliabilityAssessment(BaseModel):
    """
    Final reliability assessment produced by the
    reliability decision layer.

    This model combines:

    - standard evaluator consensus
    - adversarial resilience
    - evaluation coverage
    - critical failures
    - confidence

    It deliberately sits above individual evaluators
    and below the final report representation.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str

    overall_score: float = Field(
        ge=0,
        le=1,
    )

    standard_score: float = Field(
        ge=0,
        le=1,
    )

    adversarial_score: float = Field(
        ge=0,
        le=1,
    )

    consensus_confidence: float = Field(
        ge=0,
        le=1,
    )

    adversarial_confidence: float = Field(
        ge=0,
        le=1,
    )

    evaluation_coverage: float = Field(
        ge=0,
        le=1,
    )

    reliability_status: ReliabilityStatus

    risk_level: RiskLevel

    critical_failure_count: int = Field(
        ge=0,
    )

    adversarial_failure_count: int = Field(
        ge=0,
    )

    scenarios_run: int = Field(
        ge=0,
    )

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )