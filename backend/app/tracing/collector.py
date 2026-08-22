import uuid
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class TraceCollector:
    def __init__(
        self,
        agent_id: str,
        agent_version: str,
        task_id: str,
        task_input: Any,
        expected_output: Any = None,
    ):
        self.run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.agent_id = agent_id
        self.agent_version = agent_version
        self.task_id = task_id
        self.task = {"input": task_input, "expected_output": expected_output}
        self.events: List[Dict[str, Any]] = []
        self._start_time = time.perf_counter()

    def add_event(
        self,
        event_type: str,
        status: str = "success",
        latency_ms: Optional[float] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Records a single step in the agent execution.
        If latency_ms is omitted, it defaults to 0.0 or can be measured with `span()`.
        """
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": status,
            "latency_ms": round(latency_ms, 2) if latency_ms is not None else 0.0,
            "payload": payload or {},
        }
        self.events.append(event)
        return event["event_id"]

    @contextmanager
    def span(self, event_type: str, payload: Optional[Dict[str, Any]] = None, status: str = "success"):
        """
        Context manager that automatically measures execution latency for an event.
        
        Example:
            with collector.span("llm_call", payload={"model": "gpt-4o"}):
                response = llm.generate(...)
        """
        start = time.perf_counter()
        data = payload or {}
        try:
            yield data
        except Exception as err:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            data["error"] = str(err)
            self.add_event(event_type=event_type, status="error", latency_ms=elapsed_ms, payload=data)
            raise
        else:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.add_event(event_type=event_type, status=status, latency_ms=elapsed_ms, payload=data)

    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Automatically aggregates metrics from all recorded events.
        """
        total_latency_ms = (time.perf_counter() - self._start_time) * 1000.0
        
        # Or if events have recorded latencies, use the higher of wall clock or sum
        event_latency_sum = sum(e.get("latency_ms", 0.0) for e in self.events)
        latency_ms = max(total_latency_ms, event_latency_sum)

        input_tokens = 0
        output_tokens = 0
        llm_calls = 0
        tool_calls = 0
        estimated_cost = 0.0

        for event in self.events:
            etype = event.get("event_type", "")
            payload = event.get("payload", {})

            if "llm" in etype.lower():
                llm_calls += 1
            if "tool" in etype.lower():
                tool_calls += 1

            # Extract tokens
            in_tok = payload.get("prompt_tokens") or payload.get("input_tokens") or 0
            out_tok = payload.get("completion_tokens") or payload.get("output_tokens") or 0
            input_tokens += in_tok
            output_tokens += out_tok

            # Extract cost
            cost = payload.get("cost") or payload.get("estimated_cost")
            if cost is not None:
                estimated_cost += float(cost)
            elif in_tok or out_tok:
                # Standard approximate rate ($3/1M input, $15/1M output)
                estimated_cost += (in_tok * 0.000003) + (out_tok * 0.000015)

        return {
            "latency_ms": round(latency_ms, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "llm_calls": llm_calls,
            "tool_calls": tool_calls,
            "estimated_cost": round(estimated_cost, 6),
        }

    def export_trace(
        self,
        final_output: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> Dict[str, Any]:
        """
        Packages execution history into the exact Aegis contract format.
        Automatically calculates metrics if not explicitly provided.
        """
        computed_metrics = self.calculate_metrics()
        if metrics:
            computed_metrics.update(metrics)

        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "agent_version": self.agent_version,
            "task_id": self.task_id,
            "task": self.task,
            "events": self.events,
            "metrics": computed_metrics,
            "final_output": final_output,
            "status": status,
        }