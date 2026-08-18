from fastapi import FastAPI, Depends, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from . import models, database

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

    async def broadcast_trace(self, trace_data: dict):
        for connection in self.active_connections:
            await connection.send_json(trace_data)

manager = ConnectionManager()

# --- SCHEMAS (Keep your existing schemas here) ---
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
    traces = db.query(models.TraceRecord).order_by(models.TraceRecord.id.desc()).all()
    return traces

# --- NEW WEBSOCKET ROUTE ---
@app.websocket("/ws/traces")
async def websocket_traces(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keeps the connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- UPDATED INGEST ROUTE (Now Async) ---
@app.post("/api/traces/ingest")
async def ingest_trace(trace: TraceSchema = Body(...), db: Session = Depends(database.get_db)):
    db_trace = models.TraceRecord(
        run_id=trace.run_id,
        agent_id=trace.agent_id,
        agent_version=trace.agent_version,
        task_id=trace.task_id,
        task=trace.task.model_dump(),
        events=[event.model_dump(mode='json') for event in trace.events],
        metrics=trace.metrics.model_dump(),
        final_output=str(trace.final_output) if trace.final_output else None,
        status=trace.status
    )
    
    db.add(db_trace)
    db.commit()
    db.refresh(db_trace)
    
    # Broadcast the exact same trace dictionary to all connected browser tabs!
    await manager.broadcast_trace(trace.model_dump(mode='json'))
    
    return {"status": "success", "message": f"Trace {trace.run_id} saved and broadcasted"}