from __future__ import annotations

from uuid import uuid4

from ..core.base import BaseEvaluator
from ..core.models import (
    AgentTrace,
    EvaluationResult,
    Evidence,
    Finding,
)


class EfficiencyEvaluator(BaseEvaluator):
    """
    Evaluates execution efficiency using deterministic trace metrics.

    Dimensions:
    - latency
    - estimated cost
    - token usage
    - LLM call count
    - tool call count
    """

    name = "efficiency"

    async def evaluate(self, trace: AgentTrace) -> EvaluationResult:
        findings: list[Finding] = []
        evidence: list[Evidence] = []

        metrics = trace.metrics

        latency = metrics.latency_ms
        input_tokens = metrics.input_tokens
        output_tokens = metrics.output_tokens
        llm_calls = metrics.llm_calls
        tool_calls = metrics.tool_calls
        cost = metrics.estimated_cost

        # --------------------------------------------------
        # Individual metric scores
        # --------------------------------------------------

        latency_score = self._latency_score(latency)
        cost_score = self._cost_score(cost)
        token_score = self._token_score(
            input_tokens,
            output_tokens,
        )
        call_score = self._call_score(
            llm_calls,
            tool_calls,
        )

        # --------------------------------------------------
        # Weighted efficiency score
        # --------------------------------------------------

        score = (
            0.40 * latency_score
            + 0.25 * cost_score
            + 0.20 * token_score
            + 0.15 * call_score
        )

        score = round(score, 4)

        # --------------------------------------------------
        # Evidence
        # --------------------------------------------------

        evidence.extend(
            [
                Evidence(
                    evidence_id=str(uuid4()),
                    type="metric",
                    content=f"Latency: {latency} ms",
                    metadata={
                        "metric": "latency_ms",
                        "value": latency,
                        "score": latency_score,
                    },
                ),
                Evidence(
                    evidence_id=str(uuid4()),
                    type="metric",
                    content=f"Estimated cost: ${cost}",
                    metadata={
                        "metric": "estimated_cost",
                        "value": cost,
                        "score": cost_score,
                    },
                ),
                Evidence(
                    evidence_id=str(uuid4()),
                    type="metric",
                    content=(
                        f"Token usage: {input_tokens} input + "
                        f"{output_tokens} output"
                    ),
                    metadata={
                        "metric": "tokens",
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "score": token_score,
                    },
                ),
                Evidence(
                    evidence_id=str(uuid4()),
                    type="metric",
                    content=(
                        f"Execution calls: {llm_calls} LLM, "
                        f"{tool_calls} tool"
                    ),
                    metadata={
                        "metric": "calls",
                        "llm_calls": llm_calls,
                        "tool_calls": tool_calls,
                        "score": call_score,
                    },
                ),
            ]
        )

        # --------------------------------------------------
        # Findings
        # --------------------------------------------------

        if latency > 5000:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        f"High execution latency detected: "
                        f"{latency} ms."
                    ),
                    severity="high",
                )
            )
        elif latency > 2000:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        f"Elevated execution latency: "
                        f"{latency} ms."
                    ),
                    severity="medium",
                )
            )

        if cost > 0.01:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        f"High execution cost detected: "
                        f"${cost}."
                    ),
                    severity="high",
                )
            )
        elif cost > 0.001:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        f"Elevated execution cost: "
                        f"${cost}."
                    ),
                    severity="medium",
                )
            )

        if llm_calls > 5:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        f"Excessive LLM calls detected: "
                        f"{llm_calls}."
                    ),
                    severity="medium",
                )
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

        return EvaluationResult(
            evaluation_id=str(uuid4()),
            run_id=trace.run_id,
            evaluator=self.name,
            verdict=verdict,
            score=score,
            confidence=0.90,
            findings=findings,
            evidence=evidence,
            summary=(
                f"Efficiency score: {score:.2f}. "
                f"Latency: {latency} ms. "
                f"Cost: ${cost:.4f}."
            ),
            metadata={
                "latency_score": latency_score,
                "cost_score": cost_score,
                "token_score": token_score,
                "call_score": call_score,
            },
        )

    @staticmethod
    def _latency_score(latency: float) -> float:
        if latency <= 1000:
            return 1.0
        if latency <= 2000:
            return 0.85
        if latency <= 5000:
            return 0.60
        return 0.20

    @staticmethod
    def _cost_score(cost: float) -> float:
        if cost <= 0.001:
            return 1.0
        if cost <= 0.01:
            return 0.70
        return 0.20

    @staticmethod
    def _token_score(
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        total = input_tokens + output_tokens

        if total <= 500:
            return 1.0
        if total <= 2000:
            return 0.80
        if total <= 5000:
            return 0.50
        return 0.20

    @staticmethod
    def _call_score(
        llm_calls: int,
        tool_calls: int,
    ) -> float:
        total_calls = llm_calls + tool_calls

        if total_calls <= 3:
            return 1.0
        if total_calls <= 6:
            return 0.75
        if total_calls <= 10:
            return 0.50
        return 0.20