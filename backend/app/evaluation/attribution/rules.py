from __future__ import annotations

from dataclasses import dataclass

from ..core.models import EvaluationResult
from .models import (
    AttributionCause,
    AttributionStage,
    FailureType,
)


@dataclass(frozen=True, slots=True)
class AttributionRule:
    evaluator: str
    failure_type: FailureType
    cause: AttributionCause
    stage: AttributionStage
    confidence: float
    signal: str


RULES: tuple[AttributionRule, ...] = (
    AttributionRule(
        evaluator="correctness",
        failure_type="CORRECTNESS_FAILURE",
        cause="GENERATION_FAILURE",
        stage="GENERATION",
        confidence=0.85,
        signal="correctness evaluator reported FAIL",
    ),
    AttributionRule(
        evaluator="grounding",
        failure_type="GROUNDING_FAILURE",
        cause="RETRIEVAL_FAILURE",
        stage="RETRIEVAL",
        confidence=0.85,
        signal="grounding evaluator reported FAIL",
    ),
    AttributionRule(
        evaluator="efficiency",
        failure_type="EFFICIENCY_FAILURE",
        cause="RESOURCE_INEFFICIENCY",
        stage="POST_PROCESSING",
        confidence=0.80,
        signal="efficiency evaluator reported FAIL",
    ),
    AttributionRule(
        evaluator="safety",
        failure_type="SAFETY_FAILURE",
        cause="SAFETY_POLICY_FAILURE",
        stage="POST_PROCESSING",
        confidence=0.95,
        signal="safety evaluator reported FAIL",
    ),
    AttributionRule(
        evaluator="tool_use",
        failure_type="TOOL_USE_FAILURE",
        cause="TOOL_FAILURE",
        stage="TOOL_EXECUTION",
        confidence=0.90,
        signal="tool-use evaluator reported FAIL",
    ),
    AttributionRule(
        evaluator="robustness",
        failure_type="ROBUSTNESS_FAILURE",
        cause="ROBUSTNESS_FAILURE",
        stage="GENERATION",
        confidence=0.85,
        signal="robustness evaluator reported FAIL",
    ),
)


def find_rule(
    result: EvaluationResult,
) -> AttributionRule | None:
    """
    Resolve a deterministic attribution rule.

    Only FAIL verdicts are attributable by this rule set.
    """

    if result.verdict != "FAIL":
        return None

    for rule in RULES:
        if rule.evaluator == result.evaluator:
            return rule

    return None