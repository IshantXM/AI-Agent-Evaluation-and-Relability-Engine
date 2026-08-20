from fastapi import FastAPI, Depends, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from . import models, database
from .evaluation_bootstrap import build_agent_trace, evaluate_trace

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Aegis Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- WEBSOCKET CONNECTION MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, data: dict):
        """
        Every message on the wire is tagged with `event_type` so the
        frontend can dispatch on it. This is the seed of the full
        event vocabulary in the direction doc (TASK_STARTED,
        TOOL_CALLED, ... REPORT_READY) -- right now we only emit
        TRACE_INGESTED and REPORT_READY because that's all the
        backend produces today. Add finer-grained events once the
        agent runner emits them step-by-step instead of all at once.
        """
        message = {"event_type": event_type, "data": data}
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


# --- SCHEMAS ---
class TaskSchema(BaseModel):
    input: Any
    expected_output: Optional[Any] = None


class TraceEventSchema(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    parent_event_id: Optional[str] = None
    status: str
    latency_ms: Optional[float] = None
    payload: Optional[Dict[str, Any]] = None


class MetricsSchema(BaseModel):
    latency_ms: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    llm_calls: Optional[int] = None
    tool_calls: Optional[int] = None
    estimated_cost: Optional[float] = None


class TraceSchema(BaseModel):
    run_id: str
    agent_id: str
    agent_version: str
    task_id: str
    task: TaskSchema
    events: List[TraceEventSchema]
    metrics: MetricsSchema
    final_output: Optional[Any] = None
    status: str


# --- ROUTES ---
@app.get("/")
def read_root():
    return {"status": "Aegis Platform Engine is live!"}


@app.get("/api/traces")
def get_traces(db: Session = Depends(database.get_db)):
    return db.query(models.TraceRecord).order_by(models.TraceRecord.id.desc()).all()


@app.get("/api/evaluations")
def list_evaluations(db: Session = Depends(database.get_db)):
    return (
        db.query(models.EvaluationRecord)
        .order_by(models.EvaluationRecord.id.desc())
        .all()
    )


@app.get("/api/evaluations/{run_id}")
def get_evaluation(run_id: str, db: Session = Depends(database.get_db)):
    return (
        db.query(models.EvaluationRecord)
        .filter(models.EvaluationRecord.run_id == run_id)
        .first()
    )


@app.websocket("/ws/traces")
async def websocket_traces(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keeps the connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def _find_previous_run(
    db: Session, agent_id: str, agent_version: str
) -> Optional[models.EvaluationRecord]:
    """
    Finds the most recent evaluated run for this agent on a
    *different* version, so the report builder can compute a
    regression delta. Returns None for an agent's first-ever run
    or its first run on a new version.
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


@app.post("/api/traces/ingest")
async def ingest_trace(
    trace: TraceSchema = Body(...), db: Session = Depends(database.get_db)
):
    """
    The Milestone 2 vertical slice:

        raw trace JSON
              |
              v
        TraceRecord persisted            <- always happens, unchanged
              |
              v
        AgentTrace (evaluation engine's pydantic model)
              |
              v
        EvaluationService.evaluate()     <- Ishant's full pipeline
              |
              v
        EvaluationRecord persisted
              |
              v
        both broadcast over the websocket
    """

    trace_dict = trace.model_dump(mode="json")

    # 1. Persist the raw trace (unchanged from before)
    db_trace = models.TraceRecord(
        run_id=trace.run_id,
        agent_id=trace.agent_id,
        agent_version=trace.agent_version,
        task_id=trace.task_id,
        task=trace_dict["task"],
        events=trace_dict["events"],
        metrics=trace_dict["metrics"],
        final_output=str(trace.final_output) if trace.final_output else None,
        status=trace.status,
    )
    db.add(db_trace)
    db.commit()
    db.refresh(db_trace)

    await manager.broadcast("TRACE_INGESTED", trace_dict)

    # 2. Run it through the evaluation engine
    agent_trace = build_agent_trace(trace_dict)

    previous = _find_previous_run(db, trace.agent_id, trace.agent_version)
    previous_score = previous.overall_score if previous else None
    previous_version = previous.agent_version if previous else None

    result = await evaluate_trace(
        agent_trace,
        previous_score=previous_score,
        previous_version=previous_version,
    )

    # 3. Persist the evaluation result
    db_evaluation = models.EvaluationRecord(
        run_id=result.run_id,
        agent_id=trace.agent_id,
        agent_version=trace.agent_version,
        overall_score=result.report.overall_score,
        reliability_status=result.reliability.reliability_status,
        evaluations=[e.model_dump(mode="json") for e in result.evaluations],
        consensus=result.consensus.model_dump(mode="json"),
        adversarial_summary=result.adversarial_summary.model_dump(mode="json"),
        reliability=result.reliability.model_dump(mode="json"),
        report=result.report.model_dump(mode="json"),
    )

    # Ingesting the same run_id twice (e.g. a client retry) would
    # otherwise violate the unique constraint on run_id -- overwrite
    # instead of crashing.
    existing = (
        db.query(models.EvaluationRecord)
        .filter(models.EvaluationRecord.run_id == result.run_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()

    db.add(db_evaluation)
    db.commit()
    db.refresh(db_evaluation)

    # Broadcast the full evaluation record (same shape as
    # GET /api/evaluations/{run_id}) so the frontend doesn't need two
    # different parsing paths for "just arrived" vs "fetched on load".
    await manager.broadcast(
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
        "message": f"Trace {trace.run_id} ingested and evaluated",
        "overall_score": db_evaluation.overall_score,
        "reliability_status": db_evaluation.reliability_status,
    }
