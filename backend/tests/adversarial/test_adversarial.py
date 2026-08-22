
from datetime import datetime, timezone

import pytest

from backend.app.evaluation.adversarial.engine import AdversarialEngine
from backend.app.evaluation.adversarial.models import AdversarialScenario
from backend.app.evaluation.core.models import (
    AgentTrace,
    TaskDefinition,
    TraceEvent,
    TraceMetrics,
)
from backend.app.evaluation.adversarial.aggregator import (
    AdversarialAggregator,
)
from backend.app.evaluation.adversarial.models import (
    AdversarialResult,
)


def make_result(
    scenario_id: str,
    *,
    score: float,
    confidence: float = 0.9,
    survived: bool = True,
    recovered: bool = False,
    severity: str = "medium",
    evidence_ids: list[str] | None = None,
) -> AdversarialResult:
    return AdversarialResult(
        result_id=f"result-{scenario_id}",
        run_id="run-1",
        scenario_id=scenario_id,
        scenario_type="timeout",
        survived=survived,
        recovered=recovered,
        score=score,
        confidence=confidence,
        findings=[],
        evidence_ids=evidence_ids or [],
        metadata={
            "severity": severity,
        },
    )


def test_aggregator_handles_empty_results():
    aggregator = AdversarialAggregator()

    summary = aggregator.aggregate([])

    assert summary.scenarios_run == 0
    assert summary.overall_score == 0.0
    assert summary.confidence == 0.0
    assert summary.resilience_rate == 0.0


def test_aggregator_calculates_resilience_rate():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "s1",
            score=1.0,
            survived=True,
        ),
        make_result(
            "s2",
            score=0.0,
            survived=False,
        ),
    ]

    summary = aggregator.aggregate(results)

    assert summary.scenarios_run == 2
    assert summary.scenarios_survived == 1
    assert summary.resilience_rate == 0.5


def test_aggregator_counts_recoveries():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "s1",
            score=0.8,
            survived=True,
            recovered=True,
        ),
        make_result(
            "s2",
            score=0.2,
            survived=False,
            recovered=False,
        ),
    ]

    summary = aggregator.aggregate(results)

    assert summary.scenarios_recovered == 1


def test_aggregator_tracks_failed_scenarios():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "healthy",
            score=1.0,
            survived=True,
        ),
        make_result(
            "failed",
            score=0.1,
            survived=False,
        ),
    ]

    summary = aggregator.aggregate(results)

    assert summary.failed_scenarios == ["failed"]


def test_critical_failures_are_identified():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "critical-failure",
            score=0.1,
            survived=False,
            severity="critical",
        ),
        make_result(
            "medium-failure",
            score=0.1,
            survived=False,
            severity="medium",
        ),
    ]

    summary = aggregator.aggregate(results)

    assert summary.critical_failures == [
        "critical-failure"
    ]


def test_critical_scenario_has_higher_weight():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "critical",
            score=0.0,
            severity="critical",
        ),
        make_result(
            "low",
            score=1.0,
            severity="low",
        ),
    ]

    summary = aggregator.aggregate(results)

    # Critical weight = 3
    # Low weight = 1
    # Expected = (0*3 + 1*1) / 4 = 0.25
    assert summary.overall_score == 0.25


def test_confidence_is_averaged():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "s1",
            score=1.0,
            confidence=0.8,
        ),
        make_result(
            "s2",
            score=1.0,
            confidence=1.0,
        ),
    ]

    summary = aggregator.aggregate(results)

    assert summary.confidence == 0.9


def test_evidence_ids_are_deduplicated():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "s1",
            score=1.0,
            evidence_ids=["e1", "e2"],
        ),
        make_result(
            "s2",
            score=1.0,
            evidence_ids=["e2", "e3"],
        ),
    ]

    summary = aggregator.aggregate(results)

    assert summary.evidence_ids == [
        "e1",
        "e2",
        "e3",
    ]


def test_aggregator_output_is_deterministic():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "s1",
            score=0.8,
            confidence=0.9,
            severity="high",
        ),
        make_result(
            "s2",
            score=0.4,
            confidence=0.7,
            severity="low",
        ),
    ]

    first = aggregator.aggregate(results)
    second = aggregator.aggregate(results)

    assert first == second


def test_aggregator_score_is_bounded():
    aggregator = AdversarialAggregator()

    results = [
        make_result(
            "s1",
            score=1.0,
            severity="critical",
        ),
        make_result(
            "s2",
            score=0.0,
            severity="low",
        ),
    ]

    summary = aggregator.aggregate(results)

    assert 0.0 <= summary.overall_score <= 1.0
    assert 0.0 <= summary.confidence <= 1.0
    assert 0.0 <= summary.resilience_rate <= 1.0


def make_trace(
    *,
    status="success",
    events=None,
):
    return AgentTrace(
        run_id="run-001",
        agent_id="agent-001",
        agent_version="1.0.0",
        task_id="task-001",
        task=TaskDefinition(
            input="test input",
            expected_output="expected",
        ),
        events=events or [],
        metrics=TraceMetrics(),
        final_output="result",
        status=status,
    )


def event(
    event_id,
    event_type,
    status,
):
    return TraceEvent(
        event_id=event_id,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        status=status,
    )


def scenario(
    scenario_type,
    *,
    scenario_id=None,
    parameters=None,
    severity="medium",
):
    return AdversarialScenario(
        scenario_id=scenario_id or f"{scenario_type}-001",
        scenario_type=scenario_type,
        description=f"Test {scenario_type}",
        severity=severity,
        parameters=parameters or {},
    )


@pytest.fixture
def engine():
    return AdversarialEngine()


# ============================================================
# General engine behavior
# ============================================================


def test_engine_evaluates_multiple_scenarios(engine):
    trace = make_trace()

    scenarios = [
        scenario("timeout"),
        scenario("retry_storm"),
        scenario("tool_failure"),
        scenario("partial_execution"),
    ]

    results = engine.evaluate(trace, scenarios)

    assert len(results) == 4
    assert [result.scenario_type for result in results] == [
        "timeout",
        "retry_storm",
        "tool_failure",
        "partial_execution",
    ]

    assert all(result.run_id == trace.run_id for result in results)
    assert all(result.score >= 0 for result in results)
    assert all(result.score <= 1 for result in results)
    assert all(result.confidence >= 0 for result in results)
    assert all(result.confidence <= 1 for result in results)


def test_engine_preserves_scenario_identity(engine):
    trace = make_trace()

    scenario_input = scenario(
        "timeout",
        scenario_id="timeout-critical-42",
        severity="critical",
    )

    result = engine.evaluate(
        trace,
        [scenario_input],
    )[0]

    assert result.scenario_id == "timeout-critical-42"
    assert result.scenario_type == "timeout"
    assert result.run_id == trace.run_id


def test_engine_returns_empty_for_empty_scenarios(engine):
    trace = make_trace()

    results = engine.evaluate(trace, [])

    assert results == []


# ============================================================
# Timeout
# ============================================================


def test_timeout_without_timeout_event_is_healthy(engine):
    trace = make_trace(
        events=[
            event("e1", "agent_start", "success"),
            event("e2", "final_response", "success"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("timeout")],
    )[0]

    assert result.survived is True
    assert result.recovered is False
    assert result.score == 1.0
    assert result.confidence == 0.8
    assert result.evidence_ids == []
    assert "No timeout occurred" in result.findings[0]


def test_timeout_followed_by_success_is_recovered(engine):
    trace = make_trace(
        events=[
            event("e1", "llm_call", "timeout"),
            event("e2", "retry", "started"),
            event("e3", "llm_call", "success"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("timeout")],
    )[0]

    assert result.survived is True
    assert result.recovered is True
    assert result.score == 0.8
    assert result.evidence_ids == ["e1"]


def test_timeout_without_recovery_is_failure(engine):
    trace = make_trace(
        events=[
            event("e1", "llm_call", "timeout"),
            event("e2", "error", "failure"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("timeout")],
    )[0]

    assert result.survived is False
    assert result.recovered is False
    assert result.score == 0.2
    assert result.evidence_ids == ["e1"]


# ============================================================
# Retry storm
# ============================================================


def test_retry_behavior_within_threshold_survives(engine):
    trace = make_trace(
        events=[
            event("r1", "retry", "started"),
            event("r2", "retry", "started"),
            event("r3", "retry", "started"),
        ]
    )

    result = engine.evaluate(
        trace,
        [
            scenario(
                "retry_storm",
                parameters={"retry_threshold": 3},
            )
        ],
    )[0]

    assert result.survived is True
    assert result.recovered is True
    assert result.score == 1.0
    assert result.metadata["retry_count"] == 3
    assert result.metadata["threshold"] == 3


def test_retry_storm_above_threshold_fails(engine):
    trace = make_trace(
        events=[
            event("r1", "retry", "started"),
            event("r2", "retry", "started"),
            event("r3", "retry", "started"),
            event("r4", "retry", "started"),
        ]
    )

    result = engine.evaluate(
        trace,
        [
            scenario(
                "retry_storm",
                parameters={"retry_threshold": 3},
            )
        ],
    )[0]

    assert result.survived is False
    assert result.recovered is False
    assert result.score == 0.2
    assert result.metadata["retry_count"] == 4
    assert result.evidence_ids == [
        "r1",
        "r2",
        "r3",
        "r4",
    ]


def test_retry_storm_uses_default_threshold(engine):
    trace = make_trace(
        events=[
            event("r1", "retry", "started"),
            event("r2", "retry", "started"),
            event("r3", "retry", "started"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("retry_storm")],
    )[0]

    assert result.survived is True
    assert result.metadata["threshold"] == 3


# ============================================================
# Tool failure
# ============================================================


def test_tool_failure_without_failure_is_healthy(engine):
    trace = make_trace(
        events=[
            event("t1", "tool_result", "success"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("tool_failure")],
    )[0]

    assert result.survived is True
    assert result.recovered is False
    assert result.score == 1.0
    assert result.evidence_ids == []


def test_tool_failure_followed_by_success_recovers(engine):
    trace = make_trace(
        events=[
            event("t1", "tool_result", "failure"),
            event("t2", "tool_result", "success"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("tool_failure")],
    )[0]

    assert result.survived is True
    assert result.recovered is True
    assert result.score == 0.85
    assert result.evidence_ids == ["t1"]


def test_tool_failure_without_recovery_fails(engine):
    trace = make_trace(
        events=[
            event("t1", "tool_result", "failure"),
            event("e1", "error", "failure"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("tool_failure")],
    )[0]

    assert result.survived is False
    assert result.recovered is False
    assert result.score == 0.2
    assert result.evidence_ids == ["t1"]


# ============================================================
# Partial execution
# ============================================================


def test_successful_execution_survives_partial_execution_scenario(engine):
    trace = make_trace(status="success")

    result = engine.evaluate(
        trace,
        [scenario("partial_execution")],
    )[0]

    assert result.survived is True
    assert result.recovered is True
    assert result.score == 1.0


def test_partial_execution_is_detected(engine):
    trace = make_trace(status="partial")

    result = engine.evaluate(
        trace,
        [scenario("partial_execution")],
    )[0]

    assert result.survived is False
    assert result.recovered is False
    assert result.score == 0.3
    assert result.confidence == 0.9


# ============================================================
# Evidence integrity
# ============================================================


def test_timeout_evidence_points_to_timeout_events(engine):
    trace = make_trace(
        events=[
            event("normal", "llm_call", "success"),
            event("timeout-1", "llm_call", "timeout"),
            event("timeout-2", "tool_call", "timeout"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("timeout")],
    )[0]

    assert result.evidence_ids == [
        "timeout-1",
        "timeout-2",
    ]


def test_tool_failure_evidence_excludes_unrelated_events(engine):
    trace = make_trace(
        events=[
            event("llm-failure", "llm_call", "failure"),
            event("tool-failure", "tool_result", "failure"),
            event("tool-success", "tool_result", "success"),
        ]
    )

    result = engine.evaluate(
        trace,
        [scenario("tool_failure")],
    )[0]

    assert result.evidence_ids == ["tool-failure"]


# ============================================================
# Determinism
# ============================================================


def test_same_trace_and_scenario_produce_same_analysis(engine):
    trace = make_trace(
        events=[
            event("t1", "tool_result", "failure"),
            event("t2", "tool_result", "success"),
        ]
    )

    scenario_input = scenario("tool_failure")

    first = engine.evaluate(
        trace,
        [scenario_input],
    )[0]

    second = engine.evaluate(
        trace,
        [scenario_input],
    )[0]

    assert first.run_id == second.run_id
    assert first.scenario_id == second.scenario_id
    assert first.scenario_type == second.scenario_type
    assert first.survived == second.survived
    assert first.recovered == second.recovered
    assert first.score == second.score
    assert first.confidence == second.confidence
    assert first.findings == second.findings
    assert first.evidence_ids == second.evidence_ids
    assert first.metadata == second.metadata