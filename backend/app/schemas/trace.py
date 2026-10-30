from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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
    events: List[TraceEventSchema] = Field(default_factory=list)
    metrics: MetricsSchema = Field(default_factory=MetricsSchema)
    final_output: Optional[Any] = None
    status: str = "success"


class ScenarioGenerationRequest(BaseModel):
    domain: str
    system_prompt: Optional[str] = "You are a helpful AI assistant with access to specialized tools."
    tools: List[str] = Field(default_factory=list)
    num_scenarios: Optional[int] = 4


class ScenarioItem(BaseModel):
    scenario_id: str
    category: str
    title: str
    prompt: str
    target_evaluator: str
    severity: str
    expected_behavior: str


class ScenarioGenerationResponse(BaseModel):
    status: str
    domain: str
    tools_evaluated: List[str]
    total_scenarios_generated: int
    scenarios: List[ScenarioItem]
