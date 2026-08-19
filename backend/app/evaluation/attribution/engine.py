from __future__ import annotations

from collections.abc import Iterable

from ..core.models import EvaluationResult
from .models import (
    AttributionEvidence,
    AttributionResult,
    FailureAttribution,
)
from .rules import find_rule


class AttributionEngine:
    """
    Deterministic failure-attribution engine.

    Converts standardized evaluator failures into structured
    root-cause hypotheses.

    The attribution layer is diagnostic only. It never modifies
    evaluator results, scores, verdicts, or reliability decisions.

    Responsibilities:
    - identify failed evaluations
    - resolve deterministic attribution rules
    - preserve structured evaluator evidence
    - produce normalized attribution results

    Non-responsibilities:
    - executing evaluators
    - changing evaluator output
    - calculating reliability
    - performing model inference
    - inventing unsupported evidence
    """

    def attribute(
        self,
        *,
        run_id: str,
        evaluations: Iterable[EvaluationResult],
    ) -> AttributionResult:
        """
        Attribute failures for a single evaluation run.

        Successful evaluations are ignored.

        Failed evaluations for which no deterministic rule exists
        are deliberately left unattributed rather than receiving
        a speculative diagnosis.
        """

        results = list(evaluations)

        attributions: list[FailureAttribution] = []

        for result in results:
            rule = find_rule(result)

            if rule is None:
                continue

            evidence = self._build_evidence(
                result=result,
                rule_signal=rule.signal,
                failure_type=rule.failure_type,
            )

            attributions.append(
                FailureAttribution(
                    evaluator=result.evaluator,
                    failure_type=rule.failure_type,
                    cause=rule.cause,
                    stage=rule.stage,
                    confidence=rule.confidence,
                    evidence=evidence,
                    explanation=self._build_explanation(
                        evaluator=result.evaluator,
                        cause=rule.cause,
                        stage=rule.stage,
                    ),
                    metadata={
                        "rule_signal": rule.signal,
                        "evaluation_score": result.score,
                        "evaluation_confidence": result.confidence,
                        "source_evaluation_id": result.evaluation_id,
                    },
                )
            )

        return AttributionResult(
            run_id=run_id,
            attributions=attributions,
            metadata={
                "evaluations_processed": len(results),
                "failures_attributed": len(attributions),
                "deterministic": True,
                "unattributed_failures": sum(
                    1
                    for result in results
                    if result.verdict == "FAIL"
                    and find_rule(result) is None
                ),
            },
        )

    @staticmethod
    def _build_evidence(
        *,
        result: EvaluationResult,
        rule_signal: str,
        failure_type: str,
    ) -> list[AttributionEvidence]:
        """
        Convert evaluator output into attribution evidence.

        Existing evaluator evidence is preserved as metadata instead
        of being fabricated or discarded.
        """

        evidence: list[AttributionEvidence] = [
            AttributionEvidence(
                evaluator=result.evaluator,
                failure_type=failure_type,
                signal=rule_signal,
                value={
                    "score": result.score,
                    "verdict": result.verdict,
                    "confidence": result.confidence,
                },
                metadata={
                    "evaluation_id": result.evaluation_id,
                    "summary": result.summary,
                    "finding_count": len(result.findings),
                    "evidence_count": len(result.evidence),
                },
            )
        ]

        for item in result.evidence:
            evidence.append(
                AttributionEvidence(
                    evaluator=result.evaluator,
                    failure_type=failure_type,
                    signal=f"evaluator evidence: {item.type}",
                    value=item.content,
                    metadata={
                        "evidence_id": item.evidence_id,
                        "event_id": item.event_id,
                        "source": item.source,
                        "metadata": item.metadata,
                    },
                )
            )

        return evidence

    @staticmethod
    def _build_explanation(
        *,
        evaluator: str,
        cause: str,
        stage: str,
    ) -> str:
        cause_text = cause.lower().replace("_", " ")
        stage_text = stage.lower().replace("_", " ")

        return (
            f"{evaluator} reported a failure. "
            f"The deterministic attribution policy associates "
            f"this failure with {cause_text} during the "
            f"{stage_text} stage."
        )