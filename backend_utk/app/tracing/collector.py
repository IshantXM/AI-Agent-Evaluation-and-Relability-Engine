import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

class TraceCollector:
    def __init__(self, agent_id: str, agent_version: str, task_id: str, task_input: Any, expected_output: Any = None):
        # Automatically generate a unique run ID
        self.run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.agent_id = agent_id
        self.agent_version = agent_version
        self.task_id = task_id
        self.task = {"input": task_input, "expected_output": expected_output}
        self.events: List[Dict[str, Any]] = []
        
    def add_event(self, event_type: str, status: str, latency_ms: float = 0.0, payload: Dict[str, Any] = None):
        """Records a single step in the agent's execution journey."""
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": status,
            "latency_ms": latency_ms,
            "payload": payload or {}
        }
        self.events.append(event)
        return event["event_id"]

    def export_trace(self, final_output: str, metrics: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Packages the entire execution history into the exact Aegis contract format."""
        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "agent_version": self.agent_version,
            "task_id": self.task_id,
            "task": self.task,
            "events": self.events,
            "metrics": metrics,
            "final_output": final_output,
            "status": status
        }