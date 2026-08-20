from __future__ import annotations

from uuid import uuid4

from ..core.base import BaseEvaluator
from ..core.models import (
    AgentTrace,
    EvaluationResult,
    Evidence,
    Finding,
)


class RobustnessEvaluator(BaseEvaluator):
    """
    Evaluates an agent's ability to remain reliable under
    execution failures and recover from transient problems.

    Signals evaluated:

    - execution status
    - errors
    - retries
    - recovery after failures
    - repeated failures
    - timeouts
    - partial execution
    - suspicious retries
    - successful termination
    """

    name = "robustness"

    async def evaluate(self, trace: AgentTrace) -> EvaluationResult:
        findings: list[Finding] = []
        evidence: list[Evidence] = []

        errors = [
            event
            for event in trace.events
            if event.event_type == "error"
        ]

        retries = [
            event
            for event in trace.events
            if event.event_type == "retry"
        ]

        final_responses = [
            event
            for event in trace.events
            if event.event_type == "final_response"
        ]

        # Detect timeout using multiple representations so that
        # robustness evaluation remains framework-independent.
        timeouts = [
            event
            for event in trace.events
            if (
                event.status == "timeout"
                or (
                    event.event_type == "error"
                    and str(
                        event.payload.get("error_type", "")
                    ).lower()
                    == "timeout"
                )
            )
        ]

        # --------------------------------------------------
        # Basic execution evidence
        # --------------------------------------------------

        evidence.append(
            Evidence(
                evidence_id=str(uuid4()),
                type="metric",
                content=f"Execution status: {trace.status}",
                metadata={
                    "status": trace.status,
                    "errors": len(errors),
                    "retries": len(retries),
                    "timeouts": len(timeouts),
                    "final_responses": len(final_responses),
                },
            )
        )

        # --------------------------------------------------
        # Record error evidence
        # --------------------------------------------------

        for error in errors:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid4()),
                    type="trace_event",
                    event_id=error.event_id,
                    content="Execution error observed.",
                    metadata={
                        "event_type": error.event_type,
                        "status": error.status,
                    },
                )
            )

        # --------------------------------------------------
        # Record retry evidence
        # --------------------------------------------------

        for retry in retries:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid4()),
                    type="trace_event",
                    event_id=retry.event_id,
                    content="Agent attempted recovery through retry.",
                    metadata={
                        "event_type": retry.event_type,
                    },
                )
            )

        # --------------------------------------------------
        # Timeout handling
        # --------------------------------------------------

        if trace.status == "timeout" or timeouts:
            timeout_event_ids = [
                event.event_id
                for event in timeouts
            ]

            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        "Agent execution timeout detected. "
                        "The execution did not complete within "
                        "the expected execution window."
                    ),
                    severity="high",
                    event_ids=timeout_event_ids,
                )
            )

            evidence.append(
                Evidence(
                    evidence_id=str(uuid4()),
                    type="trace_event",
                    content="Agent execution timeout was detected.",
                    metadata={
                        "timeout": True,
                        "timeout_events": len(timeouts),
                        "event_ids": timeout_event_ids,
                    },
                )
            )

        # --------------------------------------------------
        # Partial execution
        # --------------------------------------------------

        if trace.status == "partial":
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        "Agent execution completed only partially "
                        "and did not reach a fully successful state."
                    ),
                    severity="medium",
                    event_ids=[
                        event.event_id
                        for event in trace.events
                    ],
                )
            )

        # --------------------------------------------------
        # Failed execution without recovery
        # --------------------------------------------------

        if trace.status == "failure" and errors and not retries:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        "Agent encountered execution failures "
                        "without attempting recovery."
                    ),
                    severity="high",
                    event_ids=[
                        event.event_id
                        for event in errors
                    ],
                )
            )

        # --------------------------------------------------
        # Repeated failures
        # --------------------------------------------------

        if len(errors) >= 3:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        f"Repeated execution failures detected: "
                        f"{len(errors)} errors occurred during the run."
                    ),
                    severity="high",
                    event_ids=[
                        event.event_id
                        for event in errors
                    ],
                )
            )

        elif len(errors) == 2:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        "Multiple execution failures detected "
                        "during the agent run."
                    ),
                    severity="medium",
                    event_ids=[
                        event.event_id
                        for event in errors
                    ],
                )
            )

        # --------------------------------------------------
        # Suspicious retry behavior
        # --------------------------------------------------

        if retries and not errors:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        "Retry activity was observed without a "
                        "corresponding execution error."
                    ),
                    severity="low",
                    event_ids=[
                        event.event_id
                        for event in retries
                    ],
                )
            )

        # --------------------------------------------------
        # Successful recovery
        # --------------------------------------------------

        recovered = (
            trace.status == "success"
            and len(errors) > 0
            and len(retries) > 0
            and len(final_responses) > 0
        )

        if recovered:
            evidence.append(
                Evidence(
                    evidence_id=str(uuid4()),
                    type="trace_event",
                    content=(
                        "Agent encountered failures but successfully "
                        "recovered and completed the execution."
                    ),
                    metadata={
                        "recovered": True,
                        "errors": len(errors),
                        "retries": len(retries),
                    },
                )
            )

        # --------------------------------------------------
        # Score
        # --------------------------------------------------

        score = 1.0

        if trace.status == "success":
            score = 1.0
        elif trace.status == "partial":
            score = 0.60
        elif trace.status == "timeout":
            score = 0.30
        elif trace.status == "failure":
            score = 0.20

        # Recovery improves a failed execution.
        if recovered:
            score += 0.20

        # Repeated failures reduce robustness.
        if len(errors) >= 2:
            score -= 0.15

        if len(errors) >= 3:
            score -= 0.15

        # Excessive retries are a reliability concern.
        if len(retries) >= 4:
            score -= 0.15
        elif len(retries) >= 2:
            score -= 0.05

        # Suspicious retry behavior.
        if retries and not errors:
            score -= 0.05

        # Timeout represented only at event level should
        # still negatively affect the robustness score.
        if timeouts and trace.status == "success":
            score -= 0.40

        score = max(
            0.0,
            min(1.0, round(score, 4)),
        )

        # --------------------------------------------------
        # Verdict
        # --------------------------------------------------

        if score >= 0.90:
            verdict = "PASS"
        elif score >= 0.60:
            verdict = "PARTIAL"
        else:
            verdict = "FAIL"

        # --------------------------------------------------
        # Confidence
        # --------------------------------------------------

        confidence = 0.90

        if not trace.events:
            confidence = 0.60

        if trace.status in {
            "failure",
            "timeout",
            "partial",
        }:
            confidence = 0.95

        # --------------------------------------------------
        # Result
        # --------------------------------------------------

        return EvaluationResult(
            evaluation_id=str(uuid4()),
            run_id=trace.run_id,
            evaluator=self.name,
            verdict=verdict,
            score=score,
            confidence=confidence,
            findings=findings,
            evidence=evidence,
            summary=(
                f"Robustness score: {score:.2f}. "
                f"Execution status: {trace.status}. "
                f"Errors: {len(errors)}. "
                f"Retries: {len(retries)}."
            ),
            metadata={
                "errors": len(errors),
                "retries": len(retries),
                "timeouts": len(timeouts),
                "final_responses": len(final_responses),
                "recovered": recovered,
            },
        )