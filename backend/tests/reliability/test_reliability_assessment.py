from backend.app.evaluation.adversarial.models import (
    AdversarialSummary,
)
from backend.app.evaluation.core.consensus_models import (
    ConsensusResult,
)
from backend.app.evaluation.reliability.assessor import (
    ReliabilityAssessor,
)


def make_consensus(
    *,
    score: float = 0.9,
    confidence: float = 0.9,
    status: str = "CONSISTENT",
) -> ConsensusResult:

    return ConsensusResult(
        consensus_id="consensus-1",
        run_id="run-1",
        status=status,
        consensus_score=score,
        confidence=confidence,
        assessments=[],
        conflicts=[],
        supporting_evaluation_ids=[],
        metadata={},
    )


def make_adversarial(
    *,
    score: float = 0.8,
    confidence: float = 0.9,
    resilience_rate: float = 0.8,
    failed_scenarios: list[str] | None = None,
    critical_failures: list[str] | None = None,
    scenarios_run: int = 4,
) -> AdversarialSummary:

    failed_scenarios = (
        failed_scenarios
        if failed_scenarios is not None
        else []
    )

    critical_failures = (
        critical_failures
        if critical_failures is not None
        else []
    )

    return AdversarialSummary(
        overall_score=score,
        confidence=confidence,
        resilience_rate=resilience_rate,
        scenarios_run=scenarios_run,
        scenarios_survived=(
            scenarios_run - len(failed_scenarios)
        ),
        scenarios_recovered=0,
        failed_scenarios=failed_scenarios,
        critical_failures=critical_failures,
        evidence_ids=[],
        metadata={},
    )


def test_assessor_combines_standard_and_adversarial_scores():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(score=0.9),
        adversarial=make_adversarial(score=0.6),
        evaluation_coverage=1.0,
    )

    expected = (
        0.9 * 0.70
        + 0.6 * 0.30
    )

    assert result.overall_score == round(
        expected,
        4,
    )


def test_high_score_produces_reliable_status():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(score=0.95),
        adversarial=make_adversarial(score=0.9),
        evaluation_coverage=1.0,
    )

    assert result.reliability_status == "RELIABLE"
    assert result.risk_level == "low"


def test_medium_score_produces_degraded_status():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(score=0.7),
        adversarial=make_adversarial(score=0.5),
        evaluation_coverage=1.0,
    )

    assert result.reliability_status == "DEGRADED"
    assert result.risk_level == "medium"


def test_low_score_produces_unreliable_status():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(score=0.2),
        adversarial=make_adversarial(score=0.1),
        evaluation_coverage=1.0,
    )

    assert result.reliability_status == "UNRELIABLE"
    assert result.risk_level == "critical"


def test_critical_adversarial_failure_forces_unreliable():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(score=0.95),
        adversarial=make_adversarial(
            score=0.95,
            critical_failures=["critical-timeout"],
        ),
        evaluation_coverage=1.0,
    )

    assert result.reliability_status == "UNRELIABLE"
    assert result.risk_level == "critical"
    assert result.critical_failure_count == 1


def test_insufficient_coverage_produces_insufficient_evidence():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(score=0.95),
        adversarial=make_adversarial(score=0.95),
        evaluation_coverage=0.25,
    )

    assert result.reliability_status == (
        "INSUFFICIENT_EVIDENCE"
    )


def test_zero_coverage_produces_insufficient_evidence():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(score=1.0),
        adversarial=make_adversarial(score=1.0),
        evaluation_coverage=0.0,
    )

    assert result.reliability_status == (
        "INSUFFICIENT_EVIDENCE"
    )


def test_consensus_insufficient_evidence_propagates():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(
            score=0.0,
            confidence=0.0,
            status="INSUFFICIENT_EVIDENCE",
        ),
        adversarial=make_adversarial(),
        evaluation_coverage=1.0,
    )

    assert result.reliability_status == (
        "INSUFFICIENT_EVIDENCE"
    )


def test_adversarial_failures_are_counted():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(),
        adversarial=make_adversarial(
            failed_scenarios=[
                "timeout",
                "tool-failure",
            ],
        ),
        evaluation_coverage=1.0,
    )

    assert result.adversarial_failure_count == 2


def test_scenario_count_is_preserved():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(),
        adversarial=make_adversarial(
            scenarios_run=7,
        ),
        evaluation_coverage=1.0,
    )

    assert result.scenarios_run == 7


def test_confidence_values_are_preserved():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(
            confidence=0.82,
        ),
        adversarial=make_adversarial(
            confidence=0.74,
        ),
        evaluation_coverage=1.0,
    )

    assert result.consensus_confidence == 0.82
    assert result.adversarial_confidence == 0.74


def test_coverage_is_clamped():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(),
        adversarial=make_adversarial(),
        evaluation_coverage=4.0,
    )

    assert result.evaluation_coverage == 1.0


def test_negative_coverage_is_clamped():

    assessor = ReliabilityAssessor()

    result = assessor.assess(
        consensus=make_consensus(),
        adversarial=make_adversarial(),
        evaluation_coverage=-1.0,
    )

    assert result.evaluation_coverage == 0.0


def test_assessment_is_deterministic():

    assessor = ReliabilityAssessor()

    consensus = make_consensus()
    adversarial = make_adversarial()

    first = assessor.assess(
        consensus=consensus,
        adversarial=adversarial,
        evaluation_coverage=1.0,
    )

    second = assessor.assess(
        consensus=consensus,
        adversarial=adversarial,
        evaluation_coverage=1.0,
    )

    assert first == second