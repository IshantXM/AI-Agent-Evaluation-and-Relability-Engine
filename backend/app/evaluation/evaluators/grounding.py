from __future__ import annotations

import re
from uuid import uuid4

from ..core.base import BaseEvaluator
from ..core.models import (
    AgentTrace,
    EvaluationResult,
    Evidence,
    Finding,
)


class GroundingEvaluator(BaseEvaluator):
    """
    Evaluates whether an agent's final response is supported
    by evidence present in its execution trace.

    Version 1:
    - extracts retrieval evidence from retrieval events
    - extracts simple claims from the final response
    - performs deterministic lexical support matching

    Future versions will add:
    - semantic similarity
    - contradiction detection
    - claim-level LLM judging
    """

    name = "grounding"

    async def evaluate(self, trace: AgentTrace) -> EvaluationResult:
        findings: list[Finding] = []
        evidence: list[Evidence] = []

        claims = self._extract_claims(trace.final_output)
        sources = self._extract_retrieval_sources(trace)

        # ----------------------------------------------------
        # No final answer
        # ----------------------------------------------------

        if trace.final_output is None:
            return self._build_result(
                trace=trace,
                verdict="FAIL",
                score=0.0,
                confidence=0.95,
                findings=[
                    Finding(
                        finding_id=str(uuid4()),
                        description="Agent produced no final output to evaluate.",
                        severity="high",
                    )
                ],
                evidence=evidence,
                summary="Grounding evaluation failed because no final output exists.",
            )

        # ----------------------------------------------------
        # No retrieval/evidence
        # ----------------------------------------------------

        if not sources:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    description=(
                        "No retrieval evidence was found in the agent trace."
                    ),
                    severity="medium",
                )
            )

            evidence.append(
                Evidence(
                    evidence_id=str(uuid4()),
                    type="retrieval",
                    content="No retrieval evidence found.",
                )
            )

            return self._build_result(
                trace=trace,
                verdict="NO_EVIDENCE",
                score=0.0,
                confidence=0.95,
                findings=findings,
                evidence=evidence,
                summary="No evidence was available to verify the agent response.",
            )

        # ----------------------------------------------------
        # Evaluate claims
        # ----------------------------------------------------

        supported_claims = 0
        unsupported_claims = 0

        for claim in claims:
            matched_source = self._find_supporting_source(
                claim,
                sources,
            )

            if matched_source is not None:
                supported_claims += 1

                evidence.append(
                    Evidence(
                        evidence_id=str(uuid4()),
                        type="retrieval",
                        content=matched_source,
                        metadata={
                            "claim": claim,
                            "grounding_status": "SUPPORTED",
                        },
                    )
                )

            else:
                unsupported_claims += 1

                findings.append(
                    Finding(
                        finding_id=str(uuid4()),
                        description=(
                            f"Claim is not supported by retrieved evidence: "
                            f"{claim}"
                        ),
                        severity="high",
                    )
                )

                evidence.append(
                    Evidence(
                        evidence_id=str(uuid4()),
                        type="agent_output",
                        content=claim,
                        metadata={
                            "grounding_status": "UNSUPPORTED",
                        },
                    )
                )

        # ----------------------------------------------------
        # Calculate score
        # ----------------------------------------------------

        total_claims = len(claims)

        if total_claims == 0:
            score = 1.0
            verdict = "PASS"
        else:
            score = supported_claims / total_claims

            if score == 1.0:
                verdict = "PASS"
            elif score == 0.0:
                verdict = "FAIL"
            else:
                verdict = "PARTIAL"

        return self._build_result(
            trace=trace,
            verdict=verdict,
            score=score,
            confidence=0.80,
            findings=findings,
            evidence=evidence,
            summary=(
                f"Grounding score: {score:.2f}. "
                f"Supported claims: {supported_claims}/{total_claims}."
            ),
        )

    @staticmethod
    def _extract_claims(output: object) -> list[str]:
        """
        Very small deterministic claim extractor.

        V1 treats sentences as claims.
        """

        if output is None:
            return []

        text = str(output).strip()

        if not text:
            return []

        claims = re.split(r"(?<=[.!?])\s+", text)

        return [
            claim.strip()
            for claim in claims
            if claim.strip()
        ]

    @staticmethod
    def _extract_retrieval_sources(
        trace: AgentTrace,
    ) -> list[str]:
        """
        Extract textual evidence from retrieval events.
        """

        sources: list[str] = []

        for event in trace.events:
            if event.event_type != "retrieval":
                continue

            documents = event.payload.get("documents", [])

            if isinstance(documents, list):
                for document in documents:
                    if isinstance(document, dict):
                        content = document.get("content")

                        if isinstance(content, str) and content.strip():
                            sources.append(content.strip())

                    elif isinstance(document, str):
                        sources.append(document.strip())

            content = event.payload.get("content")

            if isinstance(content, str) and content.strip():
                sources.append(content.strip())

        return sources

    @staticmethod
    def _find_supporting_source(
        claim: str,
        sources: list[str],
    ) -> str | None:
        """
        V1 lexical support matcher.

        A claim is considered supported when its normalized
        content appears within a retrieved source.

        This is deliberately conservative.
        """

        normalized_claim = GroundingEvaluator._normalize(claim)

        if not normalized_claim:
            return None

        for source in sources:
            normalized_source = GroundingEvaluator._normalize(source)

            if normalized_claim in normalized_source:
                return source

        return None

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def _build_result(
        trace: AgentTrace,
        verdict: str,
        score: float,
        confidence: float,
        findings: list[Finding],
        evidence: list[Evidence],
        summary: str,
    ) -> EvaluationResult:
        return EvaluationResult(
            evaluation_id=str(uuid4()),
            run_id=trace.run_id,
            evaluator=GroundingEvaluator.name,
            verdict=verdict,
            score=score,
            confidence=confidence,
            findings=findings,
            evidence=evidence,
            summary=summary,
        )