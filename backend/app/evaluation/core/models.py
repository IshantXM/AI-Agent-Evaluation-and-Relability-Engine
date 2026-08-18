from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Agent Trace Models
# ============================================================

EventType = Literal[
    "agent_start",
    "llm_call",
    "tool_call",
    "tool_result",
    "retrieval",
    "decision",
    "retry",
    "error",
    "final_response",
]

EventStatus = Literal[
    "started",
    "success",
    "failure",
    "timeout",
]

RunStatus = Literal[
    "success",
    "failure",
    "partial",
    "timeout",
]


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    event_type: EventType
    timestamp: datetime
    parent_event_id: str | None = None
    status: EventStatus
    latency_ms: float | None = Field(default=None, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskDefinition(BaseModel):
    model_config = ConfigDict(extra="allow")

    input: Any
    expected_output: Any | None = None


class TraceMetrics(BaseModel):
    model_config = ConfigDict(extra="allow")

    latency_ms: float = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    llm_calls: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0, ge=0)


class AgentTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    agent_id: str
    agent_version: str
    task_id: str

    task: TaskDefinition

    events: list[TraceEvent] = Field(default_factory=list)

    metrics: TraceMetrics = Field(default_factory=TraceMetrics)

    final_output: Any | None = None

    status: RunStatus


# ============================================================
# Evaluation Models
# ============================================================

EvaluatorVerdict = Literal[
    "PASS",
    "FAIL",
    "PARTIAL",
    "ERROR",
]

Severity = Literal[
    "info",
    "low",
    "medium",
    "high",
    "critical",
]


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    description: str
    severity: Severity
    event_ids: list[str] = Field(default_factory=list)


EvidenceType = Literal[
    "trace_event",
    "task",
    "agent_output",
    "tool_result",
    "retrieval",
    "metric",
    "external_reference",
]


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    type: EvidenceType
    event_id: str | None = None
    content: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluation_id: str
    run_id: str

    evaluator: str

    verdict: EvaluatorVerdict

    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)

    findings: list[Finding] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    summary: str

    metadata: dict[str, Any] = Field(default_factory=dict)