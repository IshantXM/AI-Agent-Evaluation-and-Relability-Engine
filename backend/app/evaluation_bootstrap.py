"""
Composition root for Ishant's evaluation engine.

This is the ONLY file in the platform layer that reaches into
`app.evaluation.*` internals to wire things together. Everywhere
else (main.py, database, frontend) only ever sees the two plain
functions exported here: `build_agent_trace` and `evaluate_trace`.

Why this file exists:
- The evaluation engine is intentionally dependency-injected
  (EvaluationService takes an orchestrator, critic, etc). Something
  has to construct those objects once. That's this file's only job.
- Keeping composition in one place means if Ishant adds a new
  evaluator or changes a constructor signature, there's exactly one
  place on the platform side that needs to change.
"""

from __future__ import annotations

from typing import Any

from .evaluation.core.models import (
    AgentTrace,
    TaskDefinition,
    TraceEvent,
    TraceMetrics,
)
from .evaluation.core.registry import EvaluatorRegistry
from .evaluation.evaluators.correctness import CorrectnessEvaluator
from .evaluation.evaluators.efficiency import EfficiencyEvaluator
from .evaluation.evaluators.robustness import RobustnessEvaluator
from .evaluation.evaluators.safety import SafetyEvaluator
from .evaluation.evaluators.tool_use import ToolUseEvaluator
from .evaluation.orchestration import EvaluationOrchestrator, EvaluationService

# ------------------------------------------------------------------
# Compose once, at import time. Evaluators are stateless, so a
# single shared instance is safe to reuse across every request.
# ------------------------------------------------------------------

_registry = EvaluatorRegistry()
_registry.register(CorrectnessEvaluator())
_registry.register(ToolUseEvaluator())
_registry.register(SafetyEvaluator())
_registry.register(RobustnessEvaluator())
_registry.register(EfficiencyEvaluator())

_orchestrator = EvaluationOrchestrator(_registry)
_service = EvaluationService(
    orchestrator=_orchestrator,
)


import uuid
from datetime import datetime, timezone

def build_agent_trace(trace_payload: dict[str, Any]) -> AgentTrace:
    """
    Convert raw JSON dict into validated AgentTrace object, auto-normalizing
    non-standard event types, statuses, tasks, and timestamps.
    """
    raw_task = trace_payload.get("task")
    if isinstance(raw_task, str):
        task = TaskDefinition(input=raw_task)
    elif isinstance(raw_task, dict):
        task = TaskDefinition(
            input=raw_task.get("input") or raw_task.get("prompt") or str(raw_task),
            expected_output=raw_task.get("expected_output") or raw_task.get("ground_truth"),
        )
    elif isinstance(raw_task, TaskDefinition):
        task = raw_task
    else:
        task = TaskDefinition(input=trace_payload.get("prompt") or "Autonomous Agent Task")

    valid_event_types = {
        "agent_start", "llm_call", "tool_call", "tool_result",
        "retrieval", "decision", "retry", "error", "final_response"
    }

    valid_statuses = {"started", "success", "failure", "timeout"}

    raw_events = trace_payload.get("events") or []
    normalized_events: list[TraceEvent] = []

    for idx, e in enumerate(raw_events):
        if not isinstance(e, dict):
            continue
        
        # Normalize event type
        etype = e.get("event_type", "decision").lower()
        if etype not in valid_event_types:
            if "start" in etype or "boot" in etype:
                etype = "agent_start"
            elif "llm" in etype or "model" in etype or "completion" in etype:
                etype = "llm_call"
            elif "tool_res" in etype or "result" in etype:
                etype = "tool_result"
            elif "tool" in etype or "action" in etype or "call" in etype:
                etype = "tool_call"
            elif "retrieve" in etype or "search" in etype or "rag" in etype:
                etype = "retrieval"
            elif "error" in etype or "fail" in etype:
                etype = "error"
            elif "final" in etype or "output" in etype or "response" in etype:
                etype = "final_response"
            else:
                etype = "decision"

        # Normalize status
        estatus = str(e.get("status", "success")).lower()
        if estatus not in valid_statuses:
            if estatus in ("failed", "error", "err"):
                estatus = "failure"
            elif estatus in ("start", "running", "in_progress"):
                estatus = "started"
            elif estatus in ("timed_out", "deadline_exceeded"):
                estatus = "timeout"
            else:
                estatus = "success"

        # Normalize timestamp
        ts = e.get("timestamp")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.now(timezone.utc)

        normalized_events.append(
            TraceEvent(
                event_id=e.get("event_id") or f"evt_{uuid.uuid4().hex[:8]}",
                event_type=etype,
                timestamp=dt,
                parent_event_id=e.get("parent_event_id"),
                status=estatus,
                latency_ms=max(0.0, float(e.get("latency_ms") or 0.0)),
                payload=e.get("payload") or {},
            )
        )

    # Fallback if events was empty
    if not normalized_events:
        normalized_events.append(
            TraceEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                event_type="agent_start",
                timestamp=datetime.now(timezone.utc),
                status="success",
                latency_ms=10.0,
                payload={"message": "Trace initialized"},
            )
        )

    # Normalize metrics
    raw_metrics = trace_payload.get("metrics") or {}
    metrics = TraceMetrics(
        latency_ms=float(raw_metrics.get("latency_ms") or sum(ev.latency_ms or 0 for ev in normalized_events) or 100.0),
        input_tokens=int(raw_metrics.get("input_tokens") or 100),
        output_tokens=int(raw_metrics.get("output_tokens") or 50),
        llm_calls=int(raw_metrics.get("llm_calls") or sum(1 for ev in normalized_events if ev.event_type == "llm_call")),
        tool_calls=int(raw_metrics.get("tool_calls") or sum(1 for ev in normalized_events if ev.event_type == "tool_call")),
        estimated_cost=float(raw_metrics.get("estimated_cost") or 0.001),
    )

    # Normalize run status
    r_status = str(trace_payload.get("status", "success")).lower()
    if r_status not in ("success", "failure", "partial", "timeout"):
        if r_status in ("failed", "error"):
            r_status = "failure"
        else:
            r_status = "success"

    return AgentTrace(
        run_id=trace_payload.get("run_id") or f"run_{uuid.uuid4().hex[:8]}",
        agent_id=trace_payload.get("agent_id") or "custom_agent",
        agent_version=trace_payload.get("agent_version") or "v1.0.0",
        task_id=trace_payload.get("task_id") or "task_001",
        task=task,
        events=normalized_events,
        metrics=metrics,
        final_output=trace_payload.get("final_output") or trace_payload.get("output") or "Agent task completed.",
        status=r_status,
    )



async def evaluate_trace(
    trace: AgentTrace,
    previous_score: float | None = None,
    previous_version: str | None = None,
):
    """
    Run the full evaluation pipeline (evaluators -> consensus ->
    adversarial -> reliability -> report) on a single trace.

    Returns Ishant's EvaluationRunResult dataclass. Adversarial
    scenarios are omitted for now (empty list) -- the service handles
    that gracefully, it just means adversarial_score defaults out.
    Wire real scenarios in once Milestone 5 work starts.
    """

    return await _service.evaluate(
        trace=trace,
        previous_score=previous_score,
        previous_version=previous_version,
    )


def get_evaluation_orchestrator() -> EvaluationOrchestrator:
    """Return the application-composed orchestrator for offline tools."""
    return _orchestrator
