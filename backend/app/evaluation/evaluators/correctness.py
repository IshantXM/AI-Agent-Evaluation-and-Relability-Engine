from __future__ import annotations

from typing import Any
from uuid import uuid4

from ..core.base import BaseEvaluator
from ..core.models import (
    AgentTrace,
    EvaluationResult,
    Evidence,
    Finding,
)


class CorrectnessEvaluator(BaseEvaluator):
    """
    Evaluates whether an agent completed its task correctly.

    Version 1 focuses on deterministic checks:
    - execution status
    - expected output vs actual output
    - presence of a final response
    """

    name = "correctness"

    async def evaluate(self, trace: AgentTrace) -> EvaluationResult:
        findings: list[Finding] = []
        evidence: list[Evidence] = []

        score = 1.0
        verdict = "PASS"

        # ----------------------------------------------------
        # Check 1: Agent execution status
        # ----------------------------------------------------

        if trace.status in {"failure", "timeout"}:
            score = 0.0
            verdict = "FAIL"

            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        f"Agent execution ended with status '{trace.status}'."
                    ),
                    severity="critical",
                )
            )

        # ----------------------------------------------------
        # Check 2: Final output exists
        # ----------------------------------------------------

        if trace.final_output is None:
            score = min(score, 0.2)
            verdict = "FAIL"

            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description="Agent produced no final output.",
                    severity="high",
                )
            )

        # ----------------------------------------------------
        # Check 3: Compare expected vs actual output
        # ----------------------------------------------------

        expected = trace.task.expected_output
        actual = trace.final_output

        if expected is not None and actual is not None:
            if self._outputs_match(expected, actual):
                evidence.append(
                    Evidence(
                        evidence_id=str(uuid4()),
                        type="agent_output",
                        content="Final output matches expected output.",
                    )
                )
            else:
                score = min(score, 0.0)
                verdict = "FAIL"

                findings.append(
                    Finding(
                        finding_id=str(uuid4()),
                        description=(
                            "Agent final output does not match "
                            "the expected output."
                        ),
                        severity="high",
                    )
                )

                evidence.append(
                    Evidence(
                        evidence_id=str(uuid4()),
                        type="agent_output",
                        content=f"Expected: {expected!r}; Actual: {actual!r}",
                    )
                )

        # ----------------------------------------------------
        # Determine partial result
        # ----------------------------------------------------

        if 0 < score < 1 and verdict != "FAIL":
            verdict = "PARTIAL"

        # ----------------------------------------------------
        # Build standardized result
        # ----------------------------------------------------

        return EvaluationResult(
            evaluation_id=str(uuid4()),
            run_id=trace.run_id,
            evaluator=self.name,
            verdict=verdict,
            score=score,
            confidence=0.95,
            findings=findings,
            evidence=evidence,
            summary=self._build_summary(verdict, score, findings),
        )

    @staticmethod
    def _outputs_match(expected: Any, actual: Any) -> bool:
        """
        Basic deterministic comparison.

        More sophisticated semantic evaluation will be added later.
        """

        if isinstance(expected, str) and isinstance(actual, str):
            return expected.strip().lower() == actual.strip().lower()

        return expected == actual

    @staticmethod
    def _build_summary(
        verdict: str,
        score: float,
        findings: list[Finding],
    ) -> str:
        if verdict == "PASS":
            return f"Agent passed correctness evaluation with score {score:.2f}."

        if verdict == "FAIL":
            return (
                f"Agent failed correctness evaluation with "
                f"{len(findings)} finding(s)."
            )

        return (
            f"Agent partially satisfied correctness requirements "
            f"with score {score:.2f}."
        )