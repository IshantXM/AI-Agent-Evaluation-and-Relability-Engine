from __future__ import annotations

import argparse
import statistics
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def make_sample_trace() -> dict:
    now = "2026-08-25T00:00:00Z"
    return {
        "run_id": f"benchmark_{uuid.uuid4().hex}",
        "agent_id": "benchmark-agent",
        "agent_version": "benchmark-v1",
        "task_id": "benchmark-task",
        "task": {"input": "Return the benchmark fixture result.", "expected_output": "ok"},
        "events": [
            {
                "event_id": f"event_{uuid.uuid4().hex}",
                "event_type": "agent_start",
                "timestamp": now,
                "status": "success",
                "payload": {},
            },
            {
                "event_id": f"event_{uuid.uuid4().hex}",
                "event_type": "final_response",
                "timestamp": now,
                "status": "success",
                "payload": {},
            },
        ],
        "metrics": {
            "latency_ms": 1,
            "input_tokens": 10,
            "output_tokens": 10,
            "llm_calls": 1,
            "tool_calls": 0,
            "estimated_cost": 0.0001,
        },
        "final_output": "ok",
        "status": "success",
    }


def request_once(base_url: str) -> tuple[float, bool]:
    started = time.perf_counter()
    try:
        response = requests.post(
            f"{base_url}/api/traces/ingest",
            json=make_sample_trace(),
            timeout=120,
        )
        return (time.perf_counter() - started) * 1000, response.ok
    except requests.RequestException:
        return (time.perf_counter() - started) * 1000, False


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load-test the Aegis trace ingest endpoint.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()

    started = time.perf_counter()
    results: list[tuple[float, bool]] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(request_once, args.base_url.rstrip("/")) for _ in range(args.requests)]
        for future in as_completed(futures):
            results.append(future.result())

    elapsed = time.perf_counter() - started
    latencies = [latency for latency, _ in results]
    errors = sum(not success for _, success in results)
    print("Endpoint                              Concurrency  Throughput (req/s)  P50 (ms)  P99 (ms)  Error rate")
    print(
        f"POST /api/traces/ingest               {args.concurrency:11d}  "
        f"{len(results) / elapsed:19.2f}  {percentile(latencies, 0.50):8.2f}  "
        f"{percentile(latencies, 0.99):8.2f}  {errors / len(results) * 100:9.2f}%"
    )


if __name__ == "__main__":
    main()