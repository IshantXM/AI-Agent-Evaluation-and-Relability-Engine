from __future__ import annotations

from backend.app.evaluation.reliability.models import (
    ReliabilityAssessment,
)
from backend.app.evaluation.reliability.regression import (
    ReliabilityRegressionEngine,
)


def make_assessment(
    *,
    overall_score: float = 0.90,
    standard_score: float = 0.90,
    adversarial_score: float = 0.90,
    consensus_confidence: float = 0.90,
    adversarial_confidence: float = 0.90,
    coverage: float = 1.0,
    status: str = "RELIABLE",
    risk: str = "low",
) -> ReliabilityAssessment:

    return ReliabilityAssessment(
        run_id="run-1",
        overall_score=overall_score,
        standard_score=standard_score,
        adversarial_score=adversarial_score,
        consensus_confidence=consensus_confidence,
        adversarial_confidence=adversarial_confidence,
        evaluation_coverage=coverage,
        reliability_status=status,
        risk_level=risk,
        critical_failure_count=0,
        adversarial_failure_count=0,
        scenarios_run=4,
        metadata={},
    )


def test_identical_assessments_are_unchanged():

    engine = ReliabilityRegressionEngine()

    result = engine.compare(
        previous=make_assessment(),
        current=make_assessment(),
    )

    assert result["direction"] == "UNCHANGED"
    assert result["overall_delta"] == 0.0
    assert result["regressed"] is False
    assert result["severity"] == "low"


def test_significant_score_improvement_is_detected():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        overall_score=0.70,
        status="DEGRADED",
        risk="medium",
    )

    current = make_assessment(
        overall_score=0.85,
        status="RELIABLE",
        risk="low",
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["direction"] == "IMPROVED"
    assert result["overall_delta"] == 0.15
    assert result["regressed"] is False


def test_significant_score_regression_is_detected():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        overall_score=0.90,
    )

    current = make_assessment(
        overall_score=0.70,
        status="DEGRADED",
        risk="medium",
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["direction"] == "REGRESSED"
    assert result["overall_delta"] == -0.20
    assert result["regressed"] is True
    assert result["severity"] == "critical"


def test_small_score_change_is_not_significant():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        overall_score=0.90,
    )

    current = make_assessment(
        overall_score=0.92,
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["direction"] == "UNCHANGED"
    assert result["regressed"] is False


def test_adversarial_degradation_triggers_regression():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        overall_score=0.85,
        adversarial_score=0.90,
    )

    current = make_assessment(
        overall_score=0.85,
        adversarial_score=0.80,
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["adversarial_delta"] == -0.10
    assert result["regressed"] is True


def test_confidence_degradation_triggers_regression():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        consensus_confidence=0.95,
    )

    current = make_assessment(
        consensus_confidence=0.80,
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["consensus_confidence_delta"] == -0.15
    assert result["regressed"] is True


def test_status_degradation_triggers_regression():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        status="RELIABLE",
        risk="low",
    )

    current = make_assessment(
        status="DEGRADED",
        risk="medium",
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["status_change"]["direction"] == "REGRESSED"
    assert result["risk_change"]["direction"] == "REGRESSED"
    assert result["regressed"] is True


def test_risk_escalation_triggers_regression():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        risk="medium",
    )

    current = make_assessment(
        risk="high",
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["risk_change"]["direction"] == "REGRESSED"
    assert result["regressed"] is True


def test_critical_risk_escalation_is_critical():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        overall_score=0.85,
        risk="low",
    )

    current = make_assessment(
        overall_score=0.75,
        status="DEGRADED",
        risk="critical",
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["severity"] == "critical"


def test_regression_result_is_deterministic():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        overall_score=0.90,
    )

    current = make_assessment(
        overall_score=0.70,
        status="DEGRADED",
        risk="medium",
    )

    first = engine.compare(
        previous=previous,
        current=current,
    )

    second = engine.compare(
        previous=previous,
        current=current,
    )

    assert first == second


def test_coverage_change_is_preserved():

    engine = ReliabilityRegressionEngine()

    previous = make_assessment(
        coverage=1.0,
    )

    current = make_assessment(
        coverage=0.75,
    )

    result = engine.compare(
        previous=previous,
        current=current,
    )

    assert result["coverage_delta"] == -0.25