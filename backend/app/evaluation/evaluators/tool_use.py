from __future__ import annotations

from uuid import uuid4

from ..core.base import BaseEvaluator
from ..core.models import (
    AgentTrace,
    EvaluationResult,
    Evidence,
    Finding,
)


class ToolUseEvaluator(BaseEvaluator):
    """
    Evaluates tool selection, execution, failures, and recovery
    behavior from an agent execution trace.
    """

    name = "tool_use"

    async def evaluate(self, trace: AgentTrace) -> EvaluationResult:
        findings: list[Finding] = []
        evidence: list[Evidence] = []

        tool_calls = [
            event
            for event in trace.events
            if event.event_type == "tool_call"
        ]

        tool_results = [
            event
            for event in trace.events
            if event.event_type == "tool_result"
        ]

        errors = [
            event
            for event in trace.events
            if event.event_type in {"error", "retry"}
        ]

        # --------------------------------------------------
        # No tools used
        # --------------------------------------------------

        if not tool_calls:
            return EvaluationResult(
                evaluation_id=str(uuid4()),
                run_id=trace.run_id,
                evaluator=self.name,
                verdict="PASS",
                score=1.0,
                confidence=0.95,
                findings=[],
                evidence=[
                    Evidence(
                        evidence_id=str(uuid4()),
                        type="trace_event",
                        content="No tool calls were made.",
                        metadata={
                            "tool_calls": 0,
                        },
                    )
                ],
                summary="Agent completed execution without using tools.",
            )

        # --------------------------------------------------
        # Evaluate tool calls
        # --------------------------------------------------

        successful_calls = 0
        failed_calls = 0

        for call in tool_calls:
            tool_name = call.payload.get("tool_name")

            matching_result = next(
                (
                    result
                    for result in tool_results
                    if result.parent_event_id == call.event_id
                ),
                None,
            )

            evidence.append(
                Evidence(
                    evidence_id=str(uuid4()),
                    type="trace_event",
                    event_id=call.event_id,
                    content=f"Tool called: {tool_name}",
                    metadata={
                        "tool_name": tool_name,
                    },
                )
            )

            if matching_result is None:
                failed_calls += 1

                findings.append(
                    Finding(
                        finding_id=str(uuid4()),
                        description=(
                            f"Tool '{tool_name}' was called but no "
                            "corresponding tool result was observed."
                        ),
                        severity="high",
                        event_ids=[call.event_id],
                    )
                )

                continue

            if matching_result.status in {"failure", "timeout"}:
                failed_calls += 1

                findings.append(
                    Finding(
                        finding_id=str(uuid4()),
                        description=(
                            f"Tool '{tool_name}' failed with status "
                            f"'{matching_result.status}'."
                        ),
                        severity="high",
                        event_ids=[
                            call.event_id,
                            matching_result.event_id,
                        ],
                    )
                )

            else:
                successful_calls += 1

        # --------------------------------------------------
        # Evaluate recovery
        # --------------------------------------------------

        recovered_failures = 0

        for error in errors:
            if error.event_type != "retry":
                continue

            recovered_failures += 1

            evidence.append(
                Evidence(
                    evidence_id=str(uuid4()),
                    type="trace_event",
                    event_id=error.event_id,
                    content="Agent attempted tool recovery.",
                    metadata={
                        "recovery": True,
                    },
                )
            )

        total_calls = len(tool_calls)

        score = successful_calls / total_calls

        # Recovery improves interpretation of failed execution.
        if failed_calls > 0 and recovered_failures > 0:
            score = min(
                1.0,
                score + (0.1 * recovered_failures),
            )

        if score >= 0.9:
            verdict = "PASS"
        elif score > 0:
            verdict = "PARTIAL"
        else:
            verdict = "FAIL"

        return EvaluationResult(
            evaluation_id=str(uuid4()),
            run_id=trace.run_id,
            evaluator=self.name,
            verdict=verdict,
            score=round(score, 4),
            confidence=0.85,
            findings=findings,
            evidence=evidence,
            summary=(
                f"Tool-use score: {score:.2f}. "
                f"Successful calls: {successful_calls}/{total_calls}. "
                f"Failed calls: {failed_calls}."
            ),
        )