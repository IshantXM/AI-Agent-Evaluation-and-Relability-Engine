from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


FailureType = Literal[
    "CORRECTNESS_FAILURE",
    "GROUNDING_FAILURE",
    "EFFICIENCY_FAILURE",
    "SAFETY_FAILURE",
    "TOOL_USE_FAILURE",
    "ROBUSTNESS_FAILURE",
    "ADVERSARIAL_FAILURE",
    "UNKNOWN_FAILURE",
]


AttributionCause = Literal[
    "RETRIEVAL_FAILURE",
    "GENERATION_FAILURE",
    "TOOL_FAILURE",
    "PLANNING_FAILURE",
    "SAFETY_POLICY_FAILURE",
    "RESOURCE_INEFFICIENCY",
    "ROBUSTNESS_FAILURE",
    "ADVERSARIAL_VULNERABILITY",
    "UNKNOWN_CAUSE",
]


AttributionStage = Literal[
    "INPUT",
    "PLANNING",
    "RETRIEVAL",
    "GENERATION",
    "TOOL_EXECUTION",
    "POST_PROCESSING",
    "UNKNOWN_STAGE",
]


class AttributionEvidence(BaseModel):
    """
    Evidence supporting a failure attribution.

    Evidence is intentionally structured rather than represented
    as an opaque natural-language explanation.
    """

    model_config = ConfigDict(extra="forbid")

    evaluator: str = Field(min_length=1)

    failure_type: FailureType

    signal: str = Field(min_length=1)

    value: object | None = None

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )


class FailureAttribution(BaseModel):
    """
    Root-cause attribution for one evaluation failure.

    The attribution layer explains why an evaluator failed;
    it does not replace the evaluator's verdict or score.
    """

    model_config = ConfigDict(extra="forbid")

    evaluator: str = Field(min_length=1)

    failure_type: FailureType

    cause: AttributionCause

    stage: AttributionStage

    confidence: float = Field(
        ge=0,
        le=1,
    )

    evidence: list[AttributionEvidence] = Field(
        default_factory=list,
    )

    explanation: str = Field(min_length=1)

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )


class AttributionResult(BaseModel):
    """
    Complete diagnostic attribution for one evaluation run.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)

    attributions: list[FailureAttribution] = Field(
        default_factory=list,
    )

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )