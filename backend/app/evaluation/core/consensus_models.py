from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ConsensusStatus = Literal[
    "CONSISTENT",
    "MINOR_CONFLICT",
    "MAJOR_CONFLICT",
    "INSUFFICIENT_EVIDENCE",
]


ConflictSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class EvaluatorAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluator: str
    verdict: str
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evaluation_id: str


class ConsensusConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conflict_id: str
    severity: ConflictSeverity

    description: str

    evaluators: list[str] = Field(default_factory=list)

    score_delta: float = Field(ge=0)
    evidence_ids: list[str] = Field(default_factory=list)


class ConsensusResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consensus_id: str
    run_id: str

    status: ConsensusStatus

    consensus_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)

    assessments: list[EvaluatorAssessment] = Field(
        default_factory=list
    )

    conflicts: list[ConsensusConflict] = Field(
        default_factory=list
    )

    supporting_evaluation_ids: list[str] = Field(
        default_factory=list
    )

    metadata: dict[str, object] = Field(
        default_factory=dict
    )