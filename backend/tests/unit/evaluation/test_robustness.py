import pytest

from backend.app.evaluation.core.models import AgentTrace
from backend.app.evaluation.evaluators.robustness import RobustnessEvaluator


def make_trace(
    *,
    status: str = "success",
    events: list[dict] | None = None,
) -> AgentTrace:
    return AgentTrace.model_validate(
        {
            "run_id": "run-robustness-test",
            "agent_id": "test-agent",
            "agent_version": "1.0.0",
            "task_id": "task-1",
            "task": {
                "input": "Test task",
                "expected_output": "Expected result",
            },
            "events": events or [],
            "metrics": {
                "latency_ms": 100,
                "input_tokens": 100,
                "output_tokens": 100,
                "llm_calls": 1,
                "tool_calls": 0,
                "estimated_cost": 0.001,
            },
            "final_output": "Expected result",
            "status": status,
        }
    )


@pytest.mark.asyncio
async def test_successful_execution_passes():
    trace = make_trace(
        status="success",
        events=[
            {
                "event_id": "e1",
                "event_type": "agent_start",
                "timestamp": "2026-08-18T10:00:00Z",
                "status": "started",
            },
            {
                "event_id": "e2",
                "event_type": "llm_call",
                "timestamp": "2026-08-18T10:00:01Z",
                "status": "success",
            },
            {
                "event_id": "e3",
                "event_type": "final_response",
                "timestamp": "2026-08-18T10:00:02Z",
                "status": "success",
            },
        ],
    )

    result = await RobustnessEvaluator().evaluate(trace)

    assert result.evaluator == "robustness"
    assert result.verdict == "PASS"
    assert result.score >= 0.9
    assert result.confidence > 0
    assert result.run_id == trace.run_id


@pytest.mark.asyncio
async def test_recovered_failure_is_not_treated_as_total_failure():
    trace = make_trace(
        status="success",
        events=[
            {
                "event_id": "e1",
                "event_type": "agent_start",
                "timestamp": "2026-08-18T10:00:00Z",
                "status": "started",
            },
            {
                "event_id": "e2",
                "event_type": "error",
                "timestamp": "2026-08-18T10:00:01Z",
                "status": "failure",
            },
            {
                "event_id": "e3",
                "event_type": "retry",
                "timestamp": "2026-08-18T10:00:02Z",
                "status": "started",
            },
            {
                "event_id": "e4",
                "event_type": "llm_call",
                "timestamp": "2026-08-18T10:00:03Z",
                "status": "success",
            },
            {
                "event_id": "e5",
                "event_type": "final_response",
                "timestamp": "2026-08-18T10:00:04Z",
                "status": "success",
            },
        ],
    )

    result = await RobustnessEvaluator().evaluate(trace)

    assert result.verdict in {"PASS", "PARTIAL"}
    assert result.score > 0
    assert any(
        evidence.event_id == "e3"
        for evidence in result.evidence
    )


@pytest.mark.asyncio
async def test_repeated_failures_reduce_robustness():
    trace = make_trace(
        status="failure",
        events=[
            {
                "event_id": "e1",
                "event_type": "agent_start",
                "timestamp": "2026-08-18T10:00:00Z",
                "status": "started",
            },
            {
                "event_id": "e2",
                "event_type": "error",
                "timestamp": "2026-08-18T10:00:01Z",
                "status": "failure",
            },
            {
                "event_id": "e3",
                "event_type": "retry",
                "timestamp": "2026-08-18T10:00:02Z",
                "status": "started",
            },
            {
                "event_id": "e4",
                "event_type": "error",
                "timestamp": "2026-08-18T10:00:03Z",
                "status": "failure",
            },
            {
                "event_id": "e5",
                "event_type": "retry",
                "timestamp": "2026-08-18T10:00:04Z",
                "status": "started",
            },
            {
                "event_id": "e6",
                "event_type": "error",
                "timestamp": "2026-08-18T10:00:05Z",
                "status": "failure",
            },
        ],
    )

    result = await RobustnessEvaluator().evaluate(trace)

    assert result.verdict in {"FAIL", "PARTIAL"}
    assert result.score < 0.9
    assert len(result.findings) >= 1


@pytest.mark.asyncio
async def test_timeout_is_detected():
    trace = make_trace(
        status="timeout",
        events=[
            {
                "event_id": "e1",
                "event_type": "agent_start",
                "timestamp": "2026-08-18T10:00:00Z",
                "status": "started",
            },
            {
                "event_id": "e2",
                "event_type": "error",
                "timestamp": "2026-08-18T10:00:10Z",
                "status": "timeout",
            },
        ],
    )

    result = await RobustnessEvaluator().evaluate(trace)

    assert result.verdict in {"FAIL", "PARTIAL"}
    assert result.score < 0.9

    assert any(
        "timeout" in finding.description.lower()
        for finding in result.findings
    )


@pytest.mark.asyncio
async def test_partial_execution_is_detected():
    trace = make_trace(
        status="partial",
        events=[
            {
                "event_id": "e1",
                "event_type": "agent_start",
                "timestamp": "2026-08-18T10:00:00Z",
                "status": "started",
            },
            {
                "event_id": "e2",
                "event_type": "llm_call",
                "timestamp": "2026-08-18T10:00:01Z",
                "status": "success",
            },
        ],
    )

    result = await RobustnessEvaluator().evaluate(trace)

    assert result.verdict in {"FAIL", "PARTIAL"}
    assert result.score < 0.9

    assert any(
        "partial" in finding.description.lower()
        or "incomplete" in finding.description.lower()
        for finding in result.findings
    )


@pytest.mark.asyncio
async def test_failed_execution_without_recovery_fails():
    trace = make_trace(
        status="failure",
        events=[
            {
                "event_id": "e1",
                "event_type": "agent_start",
                "timestamp": "2026-08-18T10:00:00Z",
                "status": "started",
            },
            {
                "event_id": "e2",
                "event_type": "error",
                "timestamp": "2026-08-18T10:00:01Z",
                "status": "failure",
            },
            {
                "event_id": "e3",
                "event_type": "error",
                "timestamp": "2026-08-18T10:00:02Z",
                "status": "failure",
            },
        ],
    )

    result = await RobustnessEvaluator().evaluate(trace)

    assert result.verdict == "FAIL"
    assert result.score < 0.6
    assert len(result.findings) >= 1


@pytest.mark.asyncio
async def test_retry_without_failure_is_flagged_as_suspicious():
    trace = make_trace(
        status="success",
        events=[
            {
                "event_id": "e1",
                "event_type": "agent_start",
                "timestamp": "2026-08-18T10:00:00Z",
                "status": "started",
            },
            {
                "event_id": "e2",
                "event_type": "retry",
                "timestamp": "2026-08-18T10:00:01Z",
                "status": "started",
            },
            {
                "event_id": "e3",
                "event_type": "final_response",
                "timestamp": "2026-08-18T10:00:02Z",
                "status": "success",
            },
        ],
    )

    result = await RobustnessEvaluator().evaluate(trace)

    assert len(result.findings) >= 1
    assert any(
        "retry" in finding.description.lower()
        for finding in result.findings
    )


@pytest.mark.asyncio
async def test_robustness_evidence_contains_trace_events():
    trace = make_trace(
        status="failure",
        events=[
            {
                "event_id": "e1",
                "event_type": "error",
                "timestamp": "2026-08-18T10:00:01Z",
                "status": "failure",
            },
            {
                "event_id": "e2",
                "event_type": "retry",
                "timestamp": "2026-08-18T10:00:02Z",
                "status": "started",
            },
        ],
    )

    result = await RobustnessEvaluator().evaluate(trace)

    assert len(result.evidence) >= 1

    event_ids = {
        evidence.event_id
        for evidence in result.evidence
        if evidence.event_id is not None
    }

    assert event_ids.intersection({"e1", "e2"})


@pytest.mark.asyncio
async def test_score_is_always_bounded():
    traces = [
        make_trace(status="success"),
        make_trace(status="partial"),
        make_trace(status="failure"),
        make_trace(status="timeout"),
    ]

    evaluator = RobustnessEvaluator()

    for trace in traces:
        result = await evaluator.evaluate(trace)

        assert 0.0 <= result.score <= 1.0
        assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_result_is_standardized():
    trace = make_trace()

    result = await RobustnessEvaluator().evaluate(trace)

    assert result.evaluation_id
    assert result.run_id == trace.run_id
    assert result.evaluator == "robustness"
    assert result.verdict in {
        "PASS",
        "FAIL",
        "PARTIAL",
        "ERROR",
    }
    assert isinstance(result.findings, list)
    assert isinstance(result.evidence, list)
    assert isinstance(result.summary, str)
    