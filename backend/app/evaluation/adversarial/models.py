from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AdversarialType = Literal[
    "input_perturbation",
    "tool_failure",
    "timeout",
    "retry_storm",
    "partial_execution",
    "conflicting_evidence",
]


AdversarialSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class AdversarialScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    scenario_type: AdversarialType
    description: str
    severity: AdversarialSeverity

    parameters: dict[str, object] = Field(
        default_factory=dict
    )


class AdversarialResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str

    scenario_type: AdversarialType

    survived: bool
    recovered: bool

    score: float = Field(
        ge=0,
        le=1,
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    findings: list[str] = Field(
        default_factory=list
    )

    evidence_ids: list[str] = Field(
        default_factory=list
    )

    metadata: dict[str, object] = Field(
        default_factory=dict
    )
class AdversarialSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: float = Field(
        ge=0,
        le=1,
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    resilience_rate: float = Field(
        ge=0,
        le=1,
    )

    scenarios_run: int = Field(
        ge=0,
    )

    scenarios_survived: int = Field(
        ge=0,
    )

    scenarios_recovered: int = Field(
        ge=0,
    )

    failed_scenarios: list[str] = Field(
        default_factory=list,
    )

    critical_failures: list[str] = Field(
        default_factory=list,
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )