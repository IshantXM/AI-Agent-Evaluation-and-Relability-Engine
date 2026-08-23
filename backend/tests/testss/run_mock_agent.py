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
    print("Starting simulated agent execution with automatic latency & metrics tracking...")

    collector = TraceCollector(
        agent_id="falcon_code_agent",
        agent_version="v2.1.0",
        task_id="task_algo_001",
        task_input="Write an optimized C program for matrix multiplication.",
    )

    # 1. Boot event
    with collector.span("agent_start", payload={"message": "Agent booted and parsed task parameters."}):
        time.sleep(0.15)  # Latency measured automatically!

    # 2. Tool call
    with collector.span("tool_call", payload={"tool": "search_algorithms", "query": "cache-friendly matrix mult"}):
        time.sleep(0.25)  # Latency measured automatically!

    # 3. LLM Call (measures exact inference latency + records token payload)
    print("Simulating LLM inference...")
    with collector.span("llm_call", payload={"prompt_tokens": 45, "completion_tokens": 120, "model": "gemini-1.5-pro"}):
        time.sleep(0.65)  # Latency measured automatically!

    # 4. Final Response
    with collector.span("final_response", payload={"output": "Matrix multiplication function compiled successfully."}):
        time.sleep(0.05)

    # 5. Export trace (ALL metrics: latency, token counts, LLM/tool calls, costs are calculated automatically!)
    trace_payload = collector.export_trace(
        final_output="Matrix multiplication function compiled successfully.",
        status="success",
    )

    print("\n--- Automatically Calculated Metrics ---")
    for k, v in trace_payload["metrics"].items():
        print(f"  {k}: {v}")

    print(f"\nSending trace {collector.run_id} to Aegis Ingestion API...")
    try:
        response = requests.post("http://localhost:8000/api/traces/ingest", json=trace_payload)
        if response.status_code == 200:
            result = response.json()
            print("Ingested + evaluated successfully!")
            print(f"  Overall Score: {result.get('overall_score')}")
            print(f"  Reliability Status: {result.get('reliability_status')}")
        else:
            print(f"Failed to ingest: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect. Is uvicorn running on port 8000?")



if __name__ == "__main__":
    simulate_agent_run()
