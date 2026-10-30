from __future__ import annotations

import uuid
import logging
from typing import Any, Dict, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import models
from app.core.ws_manager import ws_manager
from app.core.errors import TraceProcessingError
from app.evaluation_bootstrap import build_agent_trace, evaluate_trace

logger = logging.getLogger("aegis.trace_service")


def find_previous_run(
    db: Session, agent_id: str, agent_version: str
) -> Optional[models.EvaluationRecord]:
    """
    Finds the most recent evaluated run for this agent on a different version,
    enabling regression detection against previous versions.
    """
    return (
        db.query(models.EvaluationRecord)
        .filter(
            models.EvaluationRecord.agent_id == agent_id,
            models.EvaluationRecord.agent_version != agent_version,
        )
        .order_by(desc(models.EvaluationRecord.id))
        .first()
    )


async def evaluate_and_persist_trace(trace_dict: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Normalizes a trace dictionary, calculates missing metrics, persists to the database,
    broadcasts live updates, runs the multi-agent evaluation engine, and stores evaluation reports.
    """
    try:
        # 1. Normalize task input
        raw_task = trace_dict.get("task")
        if raw_task is None:
            trace_dict["task"] = {
                "input": trace_dict.get("prompt") or "Autonomous Agent Task"
            }
        elif isinstance(raw_task, str):
            trace_dict["task"] = {"input": raw_task}

        # 2. Derive/validate metrics
        metrics = trace_dict.get("metrics") or {}
        events = [event for event in (trace_dict.get("events") or []) if isinstance(event, dict)]
        trace_dict["events"] = events

        if not metrics.get("latency_ms"):
            metrics["latency_ms"] = round(sum(e.get("latency_ms", 0.0) for e in events) or 500.0, 2)
        if not metrics.get("llm_calls"):
            metrics["llm_calls"] = sum(1 for e in events if "llm" in e.get("event_type", "").lower())
        if not metrics.get("tool_calls"):
            metrics["tool_calls"] = sum(1 for e in events if "tool" in e.get("event_type", "").lower())
        if not metrics.get("input_tokens"):
            metrics["input_tokens"] = sum(e.get("payload", {}).get("prompt_tokens", 0) for e in events) or 100
        if not metrics.get("output_tokens"):
            metrics["output_tokens"] = sum(e.get("payload", {}).get("completion_tokens", 0) for e in events) or 50
        if not metrics.get("estimated_cost"):
            metrics["estimated_cost"] = round(
                (metrics["input_tokens"] * 0.000003) + (metrics["output_tokens"] * 0.000015), 6
            )

        trace_dict["metrics"] = metrics

        if not trace_dict.get("run_id"):
            trace_dict["run_id"] = f"run_{uuid.uuid4().hex[:8]}"

        # 3. Persist the raw trace (upsert)
        existing_trace = db.query(models.TraceRecord).filter(models.TraceRecord.run_id == trace_dict["run_id"]).first()
        if existing_trace:
            db.delete(existing_trace)
            db.commit()

        db_trace = models.TraceRecord(
            run_id=trace_dict["run_id"],
            agent_id=trace_dict.get("agent_id", "custom_agent"),
            agent_version=trace_dict.get("agent_version", "v1.0.0"),
            task_id=trace_dict.get("task_id", "custom_task"),
            task=trace_dict["task"],
            events=trace_dict["events"],
            metrics=trace_dict["metrics"],
            final_output=str(trace_dict.get("final_output", "")),
            status=trace_dict.get("status", "success"),
        )
        db.add(db_trace)
        db.commit()
        db.refresh(db_trace)

        # 4. Broadcast live ingestion
        await ws_manager.broadcast("TRACE_INGESTED", trace_dict)

        # 5. Run through AEGIS evaluation engine
        agent_trace = build_agent_trace(trace_dict)
        previous = find_previous_run(db, db_trace.agent_id, db_trace.agent_version)
        previous_score = previous.overall_score if previous else None
        previous_version = previous.agent_version if previous else None

        result = await evaluate_trace(
            agent_trace,
            previous_score=previous_score,
            previous_version=previous_version,
        )

        db_evaluation = models.EvaluationRecord(
            run_id=result.run_id,
            agent_id=db_trace.agent_id,
            agent_version=db_trace.agent_version,
            overall_score=result.report.overall_score,
            reliability_status=result.reliability.reliability_status,
            evaluations=[e.model_dump(mode="json") for e in result.evaluations],
            consensus=result.consensus.model_dump(mode="json"),
            adversarial_summary=result.adversarial_summary.model_dump(mode="json"),
            reliability=result.reliability.model_dump(mode="json"),
            report=result.report.model_dump(mode="json"),
        )

        existing_eval = db.query(models.EvaluationRecord).filter(models.EvaluationRecord.run_id == result.run_id).first()
        if existing_eval:
            db.delete(existing_eval)
            db.commit()

        db.add(db_evaluation)
        db.commit()
        db.refresh(db_evaluation)

        # 6. Broadcast completed evaluation report
        await ws_manager.broadcast(
            "REPORT_READY",
            {
                "run_id": db_evaluation.run_id,
                "agent_id": db_evaluation.agent_id,
                "agent_version": db_evaluation.agent_version,
                "overall_score": db_evaluation.overall_score,
                "reliability_status": db_evaluation.reliability_status,
                "evaluations": db_evaluation.evaluations,
                "consensus": db_evaluation.consensus,
                "adversarial_summary": db_evaluation.adversarial_summary,
                "reliability": db_evaluation.reliability,
                "report": db_evaluation.report,
            },
        )

        return {
            "status": "success",
            "run_id": db_evaluation.run_id,
            "overall_score": db_evaluation.overall_score,
            "reliability_status": db_evaluation.reliability_status,
            "report": db_evaluation.report,
        }

    except Exception as exc:
        logger.exception("Error evaluating trace: %s", exc)
        raise TraceProcessingError(f"Failed to process and evaluate trace: {str(exc)}")
