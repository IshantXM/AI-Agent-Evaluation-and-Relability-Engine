import requests
import time
from app.tracing.collector import TraceCollector

def simulate_agent_run():
    print("🤖 Starting simulated agent execution...")
    
    # 1. Initialize the collector for this specific task
    collector = TraceCollector(
        agent_id="falcon_code_agent",
        agent_version="v2.1.0",
        task_id="task_algo_001",
        task_input="Write an optimized C program for matrix multiplication."
    )
    
    # 2. Simulate Agent Start
    time.sleep(0.2)
    collector.add_event(
        event_type="agent_start", 
        status="success", 
        latency_ms=200.0, 
        payload={"message": "Agent booted and parsed task parameters."}
    )
    
    # 3. Simulate an LLM Call
    print("🧠 Thinking...")
    time.sleep(1.5)
    collector.add_event(
        event_type="llm_call", 
        status="success", 
        latency_ms=1500.0, 
        payload={"prompt_tokens": 45, "completion_tokens": 120, "model": "gemini-1.5-pro"}
    )
    
    # 4. Finalize the data payload
    trace_payload = collector.export_trace(
        final_output="Matrix multiplication function compiled successfully.",
        metrics={
            "latency_ms": 1700.0, 
            "input_tokens": 45, 
            "output_tokens": 120, 
            "llm_calls": 1,
            "tool_calls": 0,
            "estimated_cost": 0.0015
        },
        status="success"
    )
    
    # 5. Fire it to your FastAPI server!
    print(f"🚀 Sending trace {collector.run_id} to Aegis Ingestion API...")
    try:
        response = requests.post("http://localhost:8000/api/traces/ingest", json=trace_payload)
        
        if response.status_code == 200:
            print("✅ Success! Trace fully ingested. Check your Next.js dashboard!")
        else:
            print(f"❌ Failed to ingest: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to FastAPI. Is your Uvicorn server running?")

if __name__ == "__main__":
    simulate_agent_run()