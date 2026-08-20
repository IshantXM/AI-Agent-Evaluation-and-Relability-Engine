from __future__ import annotations

from ..core.models import AgentTrace
from .models import (
    AdversarialResult,
    AdversarialSummary,
)


class AdversarialAggregator:
    """
    Aggregates adversarial scenario results into a
    single resilience summary.

    The aggregator deliberately does not inspect AgentTrace
    internals. It operates only on AdversarialResult objects,
    keeping adversarial execution separate from aggregation.
    """

    SEVERITY_WEIGHTS: dict[str, float] = {
        "low": 1.0,
        "medium": 1.5,
        "high": 2.0,
        "critical": 3.0,
    }

    def aggregate(
        self,
        results: list[AdversarialResult],
    ) -> AdversarialSummary:
        """
        Aggregate adversarial results.

        Severity is obtained from result metadata. Results that
        do not contain severity default to medium severity.
        """

        if not results:
            return AdversarialSummary(
                overall_score=0.0,
                confidence=0.0,
                resilience_rate=0.0,
                scenarios_run=0,
                scenarios_survived=0,
                scenarios_recovered=0,
                failed_scenarios=[],
                critical_failures=[],
                evidence_ids=[],
                metadata={
                    "severity_weighted": True,
                    "reason": "No adversarial scenarios were evaluated.",
                },
            )

        overall_score = self._calculate_weighted_score(results)
        confidence = self._calculate_confidence(results)

        scenarios_run = len(results)

        scenarios_survived = sum(
            result.survived
            for result in results
        )

        scenarios_recovered = sum(
            result.recovered
            for result in results
        )

        resilience_rate = (
            scenarios_survived / scenarios_run
            if scenarios_run
            else 0.0
        )

        failed_scenarios = [
            result.scenario_id
            for result in results
            if not result.survived
        ]

        critical_failures = [
            result.scenario_id
            for result in results
            if self._severity(result) == "critical"
            and not result.survived
        ]

        evidence_ids = self._collect_evidence_ids(results)

        severity_counts = {
            severity: sum(
                self._severity(result) == severity
                for result in results
            )
            for severity in self.SEVERITY_WEIGHTS
        }

        return AdversarialSummary(
            overall_score=round(
                overall_score,
                4,
            ),
            confidence=round(
                confidence,
                4,
            ),
            resilience_rate=round(
                resilience_rate,
                4,
            ),
            scenarios_run=scenarios_run,
            scenarios_survived=scenarios_survived,
            scenarios_recovered=scenarios_recovered,
            failed_scenarios=failed_scenarios,
            critical_failures=critical_failures,
            evidence_ids=evidence_ids,
            metadata={
                "severity_weighted": True,
                "severity_counts": severity_counts,
                "failed_count": len(failed_scenarios),
                "critical_failure_count": len(
                    critical_failures
                ),
            },
        )

    # =========================================================
    # Score
    # =========================================================

    def _calculate_weighted_score(
        self,
        results: list[AdversarialResult],
    ) -> float:

        total_weight = 0.0
        weighted_score = 0.0

        for result in results:
            severity = self._severity(result)

            weight = self.SEVERITY_WEIGHTS[
                severity
            ]

            weighted_score += (
                result.score * weight
            )

            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_score / total_weight

    # =========================================================
    # Confidence
    # =========================================================

    @staticmethod
    def _calculate_confidence(
        results: list[AdversarialResult],
    ) -> float:

        if not results:
            return 0.0

        return (
            sum(
                result.confidence
                for result in results
            )
            / len(results)
        )

    # =========================================================
    # Severity
    # =========================================================

    def _severity(
        self,
        result: AdversarialResult,
    ) -> str:

        severity = result.metadata.get(
            "severity",
            "medium",
        )

        if severity not in self.SEVERITY_WEIGHTS:
            return "medium"

        return str(severity)

    # =========================================================
    # Evidence
    # =========================================================

    @staticmethod
    def _collect_evidence_ids(
        results: list[AdversarialResult],
    ) -> list[str]:

        evidence_ids: list[str] = []
        seen: set[str] = set()

        for result in results:
            for evidence_id in result.evidence_ids:

                if evidence_id in seen:
                    continue

                seen.add(evidence_id)
                evidence_ids.append(evidence_id)

        return evidence_ids