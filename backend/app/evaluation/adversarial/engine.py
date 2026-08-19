from __future__ import annotations

from uuid import uuid4

from ..core.models import AgentTrace
from .models import (
    AdversarialResult,
    AdversarialScenario,
)


class AdversarialEngine:
    """
    Deterministic trace-based adversarial analysis engine.

    The first-generation engine evaluates resilience using the
    recorded AgentTrace rather than mutating or re-executing the
    production agent.

    Each result preserves the originating scenario severity so that
    downstream aggregation can apply severity-aware weighting.
    """

    def evaluate(
        self,
        trace: AgentTrace,
        scenarios: list[AdversarialScenario],
    ) -> list[AdversarialResult]:
        """
        Evaluate all requested adversarial scenarios.

        Scenario ordering is preserved deliberately so that the
        output remains deterministic and traceable.
        """

        return [
            self._evaluate_scenario(
                trace=trace,
                scenario=scenario,
            )
            for scenario in scenarios
        ]

    def _evaluate_scenario(
        self,
        trace: AgentTrace,
        scenario: AdversarialScenario,
    ) -> AdversarialResult:

        if scenario.scenario_type == "timeout":
            return self._evaluate_timeout(
                trace=trace,
                scenario=scenario,
            )

        if scenario.scenario_type == "retry_storm":
            return self._evaluate_retry_storm(
                trace=trace,
                scenario=scenario,
            )

        if scenario.scenario_type == "tool_failure":
            return self._evaluate_tool_failure(
                trace=trace,
                scenario=scenario,
            )

        if scenario.scenario_type == "partial_execution":
            return self._evaluate_partial_execution(
                trace=trace,
                scenario=scenario,
            )

        return self._base_result(
            trace=trace,
            scenario=scenario,
            survived=True,
            recovered=False,
            score=0.5,
            confidence=0.5,
            findings=[
                "Scenario type is not yet actively simulated."
            ],
            metadata={
                "implemented": False,
            },
        )

    # ============================================================
    # Timeout
    # ============================================================

    def _evaluate_timeout(
        self,
        trace: AgentTrace,
        scenario: AdversarialScenario,
    ) -> AdversarialResult:

        timeout_events = [
            event
            for event in trace.events
            if event.status == "timeout"
        ]

        if not timeout_events:
            return self._base_result(
                trace=trace,
                scenario=scenario,
                survived=True,
                recovered=False,
                score=1.0,
                confidence=0.8,
                findings=[
                    "No timeout occurred during execution."
                ],
                evidence_ids=[],
            )

        recovered = any(
            event.status == "success"
            for event in trace.events
        )

        return self._base_result(
            trace=trace,
            scenario=scenario,
            survived=recovered,
            recovered=recovered,
            score=0.8 if recovered else 0.2,
            confidence=0.9,
            findings=[
                (
                    "Timeout occurred but execution recovered."
                    if recovered
                    else
                    "Timeout occurred without successful recovery."
                )
            ],
            evidence_ids=[
                event.event_id
                for event in timeout_events
            ],
        )

    # ============================================================
    # Retry storm
    # ============================================================

    def _evaluate_retry_storm(
        self,
        trace: AgentTrace,
        scenario: AdversarialScenario,
    ) -> AdversarialResult:

        retries = [
            event
            for event in trace.events
            if event.event_type == "retry"
        ]

        threshold = int(
            scenario.parameters.get(
                "retry_threshold",
                3,
            )
        )

        excessive = len(retries) > threshold

        return self._base_result(
            trace=trace,
            scenario=scenario,
            survived=not excessive,
            recovered=not excessive,
            score=0.2 if excessive else 1.0,
            confidence=0.9,
            findings=(
                ["Retry storm detected."]
                if excessive
                else
                ["Retry behavior remained bounded."]
            ),
            evidence_ids=[
                event.event_id
                for event in retries
            ],
            metadata={
                "retry_count": len(retries),
                "threshold": threshold,
            },
        )

    # ============================================================
    # Tool failure
    # ============================================================

    def _evaluate_tool_failure(
        self,
        trace: AgentTrace,
        scenario: AdversarialScenario,
    ) -> AdversarialResult:

        failures = [
            event
            for event in trace.events
            if (
                event.event_type == "tool_result"
                and event.status == "failure"
            )
        ]

        if not failures:
            return self._base_result(
                trace=trace,
                scenario=scenario,
                survived=True,
                recovered=False,
                score=1.0,
                confidence=0.85,
                findings=[
                    "No tool failure was observed."
                ],
                evidence_ids=[],
            )

        recovered = any(
            event.event_type == "tool_result"
            and event.status == "success"
            for event in trace.events
        )

        return self._base_result(
            trace=trace,
            scenario=scenario,
            survived=recovered,
            recovered=recovered,
            score=0.85 if recovered else 0.2,
            confidence=0.9,
            findings=[
                (
                    "Tool failure was followed by successful recovery."
                    if recovered
                    else
                    "Tool failure was not successfully recovered."
                )
            ],
            evidence_ids=[
                event.event_id
                for event in failures
            ],
        )

    # ============================================================
    # Partial execution
    # ============================================================

    def _evaluate_partial_execution(
        self,
        trace: AgentTrace,
        scenario: AdversarialScenario,
    ) -> AdversarialResult:

        partial = trace.status == "partial"

        return self._base_result(
            trace=trace,
            scenario=scenario,
            survived=not partial,
            recovered=not partial,
            score=0.3 if partial else 1.0,
            confidence=0.9,
            findings=(
                ["Execution ended partially."]
                if partial
                else
                ["Execution completed without partial termination."]
            ),
            evidence_ids=[],
        )

    # ============================================================
    # Result construction
    # ============================================================

    @staticmethod
    def _base_result(
        *,
        trace: AgentTrace,
        scenario: AdversarialScenario,
        survived: bool,
        recovered: bool,
        score: float,
        confidence: float,
        findings: list[str],
        evidence_ids: list[str] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AdversarialResult:
        """
        Construct a normalized adversarial result.

        Scenario severity is always propagated into metadata so the
        aggregator can apply severity-aware scoring consistently.
        """

        result_metadata = dict(
            metadata or {}
        )

        result_metadata["severity"] = (
            scenario.severity
        )

        return AdversarialResult(
            result_id=str(uuid4()),
            run_id=trace.run_id,
            scenario_id=scenario.scenario_id,
            scenario_type=scenario.scenario_type,
            survived=survived,
            recovered=recovered,
            score=score,
            confidence=confidence,
            findings=findings,
            evidence_ids=evidence_ids or [],
            metadata=result_metadata,
        )