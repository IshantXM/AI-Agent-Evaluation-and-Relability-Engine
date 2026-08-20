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
from .evaluation.evaluators.grounding import GroundingEvaluator
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
_registry.register(GroundingEvaluator())
_registry.register(ToolUseEvaluator())
_registry.register(SafetyEvaluator())
_registry.register(RobustnessEvaluator())
_registry.register(EfficiencyEvaluator())

_orchestrator = EvaluationOrchestrator(_registry)
_service = EvaluationService(orchestrator=_orchestrator)


def build_agent_trace(trace_payload: dict[str, Any]) -> AgentTrace:
    """
    Convert the raw JSON dict your ingest endpoint receives (matching
    contracts/trace.schema.json) into the pydantic AgentTrace object
    the evaluation engine actually consumes.

    Kept as a separate function (rather than inlined in main.py) so
    both the API route and any future Celery task can share it.
    """

    task = trace_payload["task"]
    if not isinstance(task, TaskDefinition):
        task = TaskDefinition(**task)

    events = [
        e if isinstance(e, TraceEvent) else TraceEvent(**e)
        for e in trace_payload.get("events", [])
    ]

    metrics = trace_payload.get("metrics", {})
    if not isinstance(metrics, TraceMetrics):
        metrics = TraceMetrics(**metrics)

    return AgentTrace(
        run_id=trace_payload["run_id"],
        agent_id=trace_payload["agent_id"],
        agent_version=trace_payload["agent_version"],
        task_id=trace_payload["task_id"],
        task=task,
        events=events,
        metrics=metrics,
        final_output=trace_payload.get("final_output"),
        status=trace_payload["status"],
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
