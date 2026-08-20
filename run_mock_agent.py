"""
Quick end-to-end smoke test. Run the API first:
    cd backend && uvicorn app.main:app --reload

Then in another terminal:
    python run_mock_agent.py

Sends a fake trace through /api/traces/ingest and prints back the
evaluation engine's verdict, so you can see Milestone 2 working
without touching the frontend.
"""
import requests
import time
from backend.app.tracing.collector import TraceCollector


def simulate_agent_run():
    print("Starting simulated agent execution...")

    collector = TraceCollector(
        agent_id="falcon_code_agent",
        agent_version="v2.1.0",
        task_id="task_algo_001",
        task_input="Write an optimized C program for matrix multiplication.",
    )

    time.sleep(0.2)
    collector.add_event(
        event_type="agent_start",
        status="success",
        latency_ms=200.0,
        payload={"message": "Agent booted and parsed task parameters."},
    )

    print("Thinking...")
    time.sleep(0.5)
    collector.add_event(
        event_type="llm_call",
        status="success",
        latency_ms=1500.0,
        payload={"prompt_tokens": 45, "completion_tokens": 120, "model": "gemini-1.5-pro"},
    )
    collector.add_event(
        event_type="final_response",
        status="success",
        latency_ms=100.0,
        payload={"output": "Matrix multiplication function compiled successfully."},
    )

    trace_payload = collector.export_trace(
        final_output="Matrix multiplication function compiled successfully.",
        metrics={
            "latency_ms": 1800.0,
            "input_tokens": 45,
            "output_tokens": 120,
            "llm_calls": 1,
            "tool_calls": 0,
            "estimated_cost": 0.0015,
        },
        status="success",
    )

    print(f"Sending trace {collector.run_id} to Aegis Ingestion API...")
    try:
        response = requests.post("http://localhost:8000/api/traces/ingest", json=trace_payload)
        if response.status_code == 200:
            print("Ingested + evaluated:", response.json())
        else:
            print(f"Failed to ingest: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect. Is uvicorn running on port 8000?")


if __name__ == "__main__":
    simulate_agent_run()
