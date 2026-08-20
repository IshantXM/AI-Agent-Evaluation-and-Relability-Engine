from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


DimensionStatus = Literal[
    "PASS",
    "FAIL",
    "PARTIAL",
    "NOT_EVALUATED",
]

RegressionStatus = Literal[
    "IMPROVED",
    "REGRESSED",
    "UNCHANGED",
    "BASELINE",
    "NOT_AVAILABLE",
]

RootCauseCategory = Literal[
    "reasoning",
    "retrieval",
    "tool_selection",
    "tool_execution",
    "grounding",
    "instruction_following",
    "safety",
    "robustness",
    "efficiency",
    "unknown",
]

Priority = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

FailureSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class DimensionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    status: DimensionStatus
    evaluation_ids: list[str] = Field(default_factory=list)


class ReportFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    failure_id: str
    severity: FailureSeverity
    description: str
    evaluator: str | None = None
    event_ids: list[str] = Field(default_factory=list)


class RootCause(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cause_id: str
    category: RootCauseCategory
    description: str
    confidence: float = Field(ge=0, le=1)
    event_ids: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str
    description: str
    priority: Priority
    related_failure_ids: list[str] = Field(default_factory=list)


class Regression(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RegressionStatus
    previous_score: float | None = Field(default=None, ge=0, le=1)
    score_delta: float | None = None
    previous_version: str | None = None


class ReliabilityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    run_id: str
    agent_id: str
    agent_version: str

    overall_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)

    dimensions: dict[str, DimensionScore]

    failures: list[ReportFailure] = Field(default_factory=list)
    root_causes: list[RootCause] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)

    regression: Regression

    metadata: dict[str, Any] = Field(default_factory=dict)