from __future__ import annotations

from typing import Literal

from .models import ReliabilityAssessment


RegressionDirection = Literal[
    "IMPROVED",
    "REGRESSED",
    "UNCHANGED",
]


class ReliabilityRegressionEngine:
    """
    Compares reliability assessments across agent versions.

    The engine is intentionally:
    - deterministic
    - side-effect free
    - independent of persistence
    - independent of report generation

    It detects regressions in:

    - overall reliability score
    - standard evaluation score
    - adversarial resilience
    - consensus confidence
    - adversarial confidence
    - evaluation coverage
    - reliability status
    - operational risk

    A regression is only considered numerically significant when
    the absolute change is >= SIGNIFICANCE_THRESHOLD.
    """

    SIGNIFICANCE_THRESHOLD = 0.05

    STATUS_RANK = {
        "INSUFFICIENT_EVIDENCE": 0,
        "UNRELIABLE": 1,
        "DEGRADED": 2,
        "RELIABLE": 3,
    }

    RISK_RANK = {
        "low": 0,
        "medium": 1,
        "high": 2,
        "critical": 3,
    }

    def compare(
        self,
        *,
        previous: ReliabilityAssessment,
        current: ReliabilityAssessment,
    ) -> dict[str, object]:
        """
        Compare two reliability assessments.

        Returns a deterministic regression summary.
        """

        overall_delta = (
            current.overall_score
            - previous.overall_score
        )

        standard_delta = (
            current.standard_score
            - previous.standard_score
        )

        adversarial_delta = (
            current.adversarial_score
            - previous.adversarial_score
        )

        consensus_confidence_delta = (
            current.consensus_confidence
            - previous.consensus_confidence
        )

        adversarial_confidence_delta = (
            current.adversarial_confidence
            - previous.adversarial_confidence
        )

        coverage_delta = (
            current.evaluation_coverage
            - previous.evaluation_coverage
        )

        status_change = self._compare_status(
            previous.reliability_status,
            current.reliability_status,
        )

        risk_change = self._compare_risk(
            previous.risk_level,
            current.risk_level,
        )

        return {
            "direction": self._direction(
                overall_delta
            ),
            "overall_delta": round(
                overall_delta,
                4,
            ),
            "standard_delta": round(
                standard_delta,
                4,
            ),
            "adversarial_delta": round(
                adversarial_delta,
                4,
            ),
            "consensus_confidence_delta": round(
                consensus_confidence_delta,
                4,
            ),
            "adversarial_confidence_delta": round(
                adversarial_confidence_delta,
                4,
            ),
            "coverage_delta": round(
                coverage_delta,
                4,
            ),
            "status_change": status_change,
            "risk_change": risk_change,
            "regressed": self._is_regressed(
                previous=previous,
                current=current,
                overall_delta=overall_delta,
                adversarial_delta=adversarial_delta,
                consensus_confidence_delta=(
                    consensus_confidence_delta
                ),
                adversarial_confidence_delta=(
                    adversarial_confidence_delta
                ),
            ),
            "severity": self._determine_severity(
                previous=previous,
                current=current,
                overall_delta=overall_delta,
                status_change=status_change,
                risk_change=risk_change,
            ),
            "metadata": {
                "previous_run_id": previous.run_id,
                "current_run_id": current.run_id,
                "significance_threshold": (
                    self.SIGNIFICANCE_THRESHOLD
                ),
            },
        }

    # ============================================================
    # Numeric direction
    # ============================================================

    @classmethod
    def _direction(
        cls,
        delta: float,
    ) -> RegressionDirection:
        if delta >= cls.SIGNIFICANCE_THRESHOLD:
            return "IMPROVED"

        if delta <= -cls.SIGNIFICANCE_THRESHOLD:
            return "REGRESSED"

        return "UNCHANGED"

    # ============================================================
    # Status comparison
    # ============================================================

    @classmethod
    def _compare_status(
        cls,
        previous: str,
        current: str,
    ) -> dict[str, object]:

        previous_rank = cls.STATUS_RANK.get(
            previous,
            0,
        )

        current_rank = cls.STATUS_RANK.get(
            current,
            0,
        )

        if current_rank < previous_rank:
            direction = "REGRESSED"

        elif current_rank > previous_rank:
            direction = "IMPROVED"

        else:
            direction = "UNCHANGED"

        return {
            "previous": previous,
            "current": current,
            "direction": direction,
        }

    # ============================================================
    # Risk comparison
    # ============================================================

    @classmethod
    def _compare_risk(
        cls,
        previous: str,
        current: str,
    ) -> dict[str, object]:

        previous_rank = cls.RISK_RANK.get(
            previous,
            0,
        )

        current_rank = cls.RISK_RANK.get(
            current,
            0,
        )

        if current_rank > previous_rank:
            direction = "REGRESSED"

        elif current_rank < previous_rank:
            direction = "IMPROVED"

        else:
            direction = "UNCHANGED"

        return {
            "previous": previous,
            "current": current,
            "direction": direction,
        }

    # ============================================================
    # Regression detection
    # ============================================================

    @classmethod
    def _is_regressed(
        cls,
        *,
        previous: ReliabilityAssessment,
        current: ReliabilityAssessment,
        overall_delta: float,
        adversarial_delta: float,
        consensus_confidence_delta: float,
        adversarial_confidence_delta: float,
    ) -> bool:

        # Significant overall degradation.
        if overall_delta <= -cls.SIGNIFICANCE_THRESHOLD:
            return True

        # Significant adversarial degradation.
        if adversarial_delta <= -cls.SIGNIFICANCE_THRESHOLD:
            return True

        # Significant confidence degradation.
        if (
            consensus_confidence_delta
            <= -cls.SIGNIFICANCE_THRESHOLD
        ):
            return True

        if (
            adversarial_confidence_delta
            <= -cls.SIGNIFICANCE_THRESHOLD
        ):
            return True

        # Reliability status degradation.
        previous_status = cls.STATUS_RANK.get(
            previous.reliability_status,
            0,
        )

        current_status = cls.STATUS_RANK.get(
            current.reliability_status,
            0,
        )

        if current_status < previous_status:
            return True

        # Risk escalation.
        previous_risk = cls.RISK_RANK.get(
            previous.risk_level,
            0,
        )

        current_risk = cls.RISK_RANK.get(
            current.risk_level,
            0,
        )

        if current_risk > previous_risk:
            return True

        return False

    # ============================================================
    # Severity
    # ============================================================

    @classmethod
    def _determine_severity(
        cls,
        *,
        previous: ReliabilityAssessment,
        current: ReliabilityAssessment,
        overall_delta: float,
        status_change: dict[str, object],
        risk_change: dict[str, object],
    ) -> str:

        # Critical risk escalation is always critical.
        if (
            current.risk_level == "critical"
            and previous.risk_level != "critical"
        ):
            return "critical"

        # Reliability collapsing to unreliable is critical.
        if (
            current.reliability_status == "UNRELIABLE"
            and previous.reliability_status
            in {
                "RELIABLE",
                "DEGRADED",
            }
        ):
            return "critical"

        # Large score regression.
        if overall_delta <= -0.20:
            return "critical"

        if overall_delta <= -0.10:
            return "high"

        if (
            status_change["direction"] == "REGRESSED"
            or risk_change["direction"] == "REGRESSED"
        ):
            return "high"

        if overall_delta <= -cls.SIGNIFICANCE_THRESHOLD:
            return "medium"

        return "low"