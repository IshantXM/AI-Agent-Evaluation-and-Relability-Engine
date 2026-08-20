from __future__ import annotations

from ..adversarial.models import AdversarialSummary
from ..core.consensus_models import ConsensusResult
from .models import ReliabilityAssessment


class ReliabilityAssessor:
    """
    Deterministic decision layer for unified agent reliability.

    The assessor combines two independent signals:

        Standard evaluation consensus
                    +
        Adversarial resilience
                    ↓
        Unified reliability assessment

    Responsibilities:
    - combine standard and adversarial scores
    - enforce evaluation-coverage gates
    - propagate insufficient-evidence states
    - escalate critical adversarial failures
    - classify reliability status
    - classify operational risk
    - preserve confidence and provenance metadata

    Non-responsibilities:
    - executing evaluators
    - executing adversarial scenarios
    - generating reports
    - modifying traces
    - performing model inference

    The class is intentionally deterministic and side-effect free.
    """

    # ============================================================
    # Score composition
    # ============================================================

    STANDARD_WEIGHT: float = 0.70
    ADVERSARIAL_WEIGHT: float = 0.30

    # ============================================================
    # Reliability status policy
    # ============================================================

    RELIABLE_THRESHOLD: float = 0.80
    DEGRADED_THRESHOLD: float = 0.60

    # ============================================================
    # Risk policy
    #
    # Risk is intentionally independent from reliability status.
    # A run can be RELIABLE but still carry medium risk at the
    # boundary, while a DEGRADED run is inherently medium risk.
    # ============================================================

    LOW_RISK_THRESHOLD: float = 0.80
    MEDIUM_RISK_THRESHOLD: float = 0.60
    HIGH_RISK_THRESHOLD: float = 0.40
    CRITICAL_RISK_THRESHOLD: float = 0.20

    # ============================================================
    # Coverage policy
    # ============================================================

    MINIMUM_COVERAGE: float = 0.50

    # ============================================================
    # Public API
    # ============================================================

    def assess(
        self,
        *,
        consensus: ConsensusResult,
        adversarial: AdversarialSummary,
        evaluation_coverage: float,
    ) -> ReliabilityAssessment:
        """
        Produce a unified reliability assessment.

        The calculation is:

            overall =
                standard_score * STANDARD_WEIGHT
                +
                adversarial_score * ADVERSARIAL_WEIGHT

        Evaluation coverage does not modify the numerical score.
        Instead, coverage acts as an evidence-quality gate.

        Critical adversarial failures override the numerical score
        and force an UNRELIABLE / critical-risk assessment.
        """

        coverage = self._clamp(evaluation_coverage)

        standard_score = self._clamp(
            consensus.consensus_score
        )

        adversarial_score = self._clamp(
            adversarial.overall_score
        )

        overall_score = self._calculate_overall_score(
            standard_score=standard_score,
            adversarial_score=adversarial_score,
        )

        critical_failure_count = len(
            adversarial.critical_failures
        )

        adversarial_failure_count = len(
            adversarial.failed_scenarios
        )

        reliability_status = self._determine_status(
            overall_score=overall_score,
            evaluation_coverage=coverage,
            consensus=consensus,
            critical_failure_count=critical_failure_count,
        )

        risk_level = self._determine_risk(
            overall_score=overall_score,
            critical_failure_count=critical_failure_count,
        )

        return ReliabilityAssessment(
            run_id=consensus.run_id,

            overall_score=round(
                overall_score,
                4,
            ),

            standard_score=round(
                standard_score,
                4,
            ),

            adversarial_score=round(
                adversarial_score,
                4,
            ),

            consensus_confidence=round(
                self._clamp(
                    consensus.confidence
                ),
                4,
            ),

            adversarial_confidence=round(
                self._clamp(
                    adversarial.confidence
                ),
                4,
            ),

            evaluation_coverage=round(
                coverage,
                4,
            ),

            reliability_status=reliability_status,

            risk_level=risk_level,

            critical_failure_count=critical_failure_count,

            adversarial_failure_count=adversarial_failure_count,

            scenarios_run=adversarial.scenarios_run,

            metadata={
                "standard_weight": self.STANDARD_WEIGHT,
                "adversarial_weight": self.ADVERSARIAL_WEIGHT,

                "consensus_status": consensus.status,

                "adversarial_resilience_rate": (
                    self._clamp(
                        adversarial.resilience_rate
                    )
                ),

                "coverage_gate_passed": (
                    coverage >= self.MINIMUM_COVERAGE
                ),

                "critical_failure_override": (
                    critical_failure_count > 0
                ),

                "risk_policy": {
                    "low": (
                        f">= {self.LOW_RISK_THRESHOLD:.2f}"
                    ),
                    "medium": (
                        f"{self.MEDIUM_RISK_THRESHOLD:.2f}"
                        f" <= score < "
                        f"{self.LOW_RISK_THRESHOLD:.2f}"
                    ),
                    "high": (
                        f"{self.CRITICAL_RISK_THRESHOLD:.2f}"
                        f" <= score < "
                        f"{self.MEDIUM_RISK_THRESHOLD:.2f}"
                    ),
                    "critical": (
                        f"< {self.CRITICAL_RISK_THRESHOLD:.2f}"
                    ),
                },
            },
        )

    # ============================================================
    # Score calculation
    # ============================================================

    @classmethod
    def _calculate_overall_score(
        cls,
        *,
        standard_score: float,
        adversarial_score: float,
    ) -> float:
        """
        Calculate the weighted reliability score.

        Keeping this calculation isolated makes the scoring policy
        easy to test independently and easy to evolve later.
        """

        score = (
            standard_score * cls.STANDARD_WEIGHT
            + adversarial_score * cls.ADVERSARIAL_WEIGHT
        )

        return cls._clamp(score)

    # ============================================================
    # Reliability status
    # ============================================================

    @classmethod
    def _determine_status(
        cls,
        *,
        overall_score: float,
        evaluation_coverage: float,
        consensus: ConsensusResult,
        critical_failure_count: int,
    ) -> str:
        """
        Determine the final reliability classification.

        Decision precedence:

            1. No coverage
            2. Consensus lacks evidence
            3. Critical adversarial failure
            4. Insufficient coverage
            5. Numerical reliability score
        """

        if evaluation_coverage <= 0.0:
            return "INSUFFICIENT_EVIDENCE"

        if consensus.status == "INSUFFICIENT_EVIDENCE":
            return "INSUFFICIENT_EVIDENCE"

        if critical_failure_count > 0:
            return "UNRELIABLE"

        if evaluation_coverage < cls.MINIMUM_COVERAGE:
            return "INSUFFICIENT_EVIDENCE"

        if overall_score >= cls.RELIABLE_THRESHOLD:
            return "RELIABLE"

        if overall_score >= cls.DEGRADED_THRESHOLD:
            return "DEGRADED"

        return "UNRELIABLE"

    # ============================================================
    # Risk classification
    # ============================================================

    @classmethod
    def _determine_risk(
        cls,
        *,
        overall_score: float,
        critical_failure_count: int,
    ) -> str:
        """
        Classify operational risk independently of reliability status.

        Policy:

            score >= 0.80  -> low
            0.60 - <0.80   -> medium
            0.40 - <0.60   -> high
            0.20 - <0.40   -> high
            score < 0.20   -> critical

        Critical adversarial failures always override score-based
        classification.
        """

        if critical_failure_count > 0:
            return "critical"

        if overall_score < cls.CRITICAL_RISK_THRESHOLD:
            return "critical"

        if overall_score < cls.MEDIUM_RISK_THRESHOLD:
            return "high"

        if overall_score < cls.LOW_RISK_THRESHOLD:
            return "medium"

        return "low"

    # ============================================================
    # Numeric safety
    # ============================================================

    @staticmethod
    def _clamp(
        value: float,
    ) -> float:
        """
        Clamp a score/confidence/coverage value into [0, 1].

        This protects the decision layer from malformed upstream
        values without mutating the original models.
        """

        return max(
            0.0,
            min(
                1.0,
                float(value),
            ),
        )