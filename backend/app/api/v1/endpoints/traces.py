from __future__ import annotations

import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Body, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app import models, database
from app.schemas.trace import TraceSchema
from app.services.trace_service import evaluate_and_persist_trace

router = APIRouter(prefix="/traces", tags=["Traces"])


@router.get("", response_model=List[Dict[str, Any]])
def get_traces(db: Session = Depends(database.get_db)):
    """Fetch historical ingested traces ordered by recency."""
    traces = db.query(models.TraceRecord).order_by(models.TraceRecord.id.desc()).all()
    return [
        {
            "id": t.id,
            "run_id": t.run_id,
            "agent_id": t.agent_id,
            "agent_version": t.agent_version,
            "task_id": t.task_id,
            "task": t.task,
            "events": t.events,
            "metrics": t.metrics,
            "final_output": t.final_output,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in traces
    ]


@router.post("/ingest")
async def ingest_trace(
    trace: TraceSchema = Body(...), db: Session = Depends(database.get_db)
):
    """
    Ingest a single structured trace, persist it, broadcast live websocket events,
    and run through the multi-agent evaluation pipeline.
    """
    trace_dict = trace.model_dump(mode="json")
    return await evaluate_and_persist_trace(trace_dict, db)


@router.post("/upload")
async def upload_trace_file(
    file: UploadFile = File(...), db: Session = Depends(database.get_db)
):
    """
    Accepts uploaded .json or .jsonl trace files (single trace or batch array).
    Evaluates each trace in real time, saves to database, and broadcasts live results.
    """
    try:
        content = await file.read()
        filename = file.filename or "trace.json"
        if not content.strip():
            raise HTTPException(status_code=422, detail="The uploaded trace file is empty")

        results = []
        if filename.lower().endswith(".jsonl"):
            lines = content.decode("utf-8").strip().split("\n")
            for line in lines:
                if line.strip():
                    item = json.loads(line.strip())
                    res = await evaluate_and_persist_trace(item, db)
                    results.append(res)
        else:
            payload = json.loads(content.decode("utf-8"))
            if isinstance(payload, list):
                for item in payload:
                    res = await evaluate_and_persist_trace(item, db)
                    results.append(res)
            elif isinstance(payload, dict):
                if "events" in payload and "task" in payload:
                    res = await evaluate_and_persist_trace(payload, db)
                    results.append(res)
                elif "cases" in payload:
                    for case in payload["cases"]:
                        res = await evaluate_and_persist_trace(case, db)
                        results.append(res)
                else:
                    res = await evaluate_and_persist_trace(payload, db)
                    results.append(res)

        return {
            "status": "success",
            "file_processed": filename,
            "traces_evaluated_count": len(results),
            "results": results,
        }
    except HTTPException:
        raise
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON trace file: {exc.msg}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse and evaluate trace file: {str(exc)}")
