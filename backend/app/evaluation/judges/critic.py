from __future__ import annotations

from itertools import combinations
from uuid import uuid4

from ..core.consensus_models import (
    ConsensusConflict,
    ConsensusResult,
    EvaluatorAssessment,
)
from ..core.models import EvaluationResult


class CriticAgent:
    """
    Deterministic cross-evaluator critic.

    Individual evaluators answer:
        "How well did the agent perform on this dimension?"

    The critic answers:
        "Are the evaluator conclusions internally consistent,
        sufficiently supported, and trustworthy as a group?"

    Responsibilities:
    - detect contradictory evaluator verdicts
    - detect large score disagreements
    - account for evaluator confidence
    - identify insufficient evidence
    - calculate confidence-weighted consensus
    - preserve links to evaluator evidence
    """

    SCORE_CONFLICT_THRESHOLD = 0.40

    def evaluate(
        self,
        results: list[EvaluationResult],
    ) -> ConsensusResult:

        if not results:
            return ConsensusResult(
                consensus_id=str(uuid4()),
                run_id="unknown",
                status="INSUFFICIENT_EVIDENCE",
                consensus_score=0.0,
                confidence=0.0,
                assessments=[],
                conflicts=[],
                supporting_evaluation_ids=[],
                metadata={
                    "evaluators": 0,
                    "reason": "No evaluation results were provided.",
                },
            )

        run_id = results[0].run_id

        assessments = [
            EvaluatorAssessment(
                evaluator=result.evaluator,
                verdict=result.verdict,
                score=result.score,
                confidence=result.confidence,
                evaluation_id=result.evaluation_id,
            )
            for result in results
        ]

        conflicts = self._detect_conflicts(results)

        consensus_score = self._calculate_consensus_score(
            results
        )

        confidence = self._calculate_confidence(
            results,
            conflicts,
        )

        status = self._determine_status(
            results,
            conflicts,
        )

        supporting_ids = [
            result.evaluation_id
            for result in results
            if result.confidence >= 0.70
            and result.verdict != "ERROR"
        ]

        return ConsensusResult(
            consensus_id=str(uuid4()),
            run_id=run_id,
            status=status,
            consensus_score=round(
                consensus_score,
                4,
            ),
            confidence=round(
                confidence,
                4,
            ),
            assessments=assessments,
            conflicts=conflicts,
            supporting_evaluation_ids=supporting_ids,
            metadata={
                "evaluators": len(results),
                "conflicts": len(conflicts),
                "high_confidence_evaluators": len(
                    supporting_ids
                ),
                "error_evaluators": sum(
                    result.verdict == "ERROR"
                    for result in results
                ),
            },
        )

    # ---------------------------------------------------------
    # Conflict detection
    # ---------------------------------------------------------

    def _detect_conflicts(
        self,
        results: list[EvaluationResult],
    ) -> list[ConsensusConflict]:

        conflicts: list[ConsensusConflict] = []

        for left, right in combinations(results, 2):

            score_delta = abs(
                left.score - right.score
            )

            verdict_conflict = self._verdicts_conflict(
                left.verdict,
                right.verdict,
            )

            large_score_difference = (
                score_delta >= self.SCORE_CONFLICT_THRESHOLD
            )

            if (
                not verdict_conflict
                and not large_score_difference
            ):
                continue

            severity = self._conflict_severity(
                score_delta=score_delta,
                verdict_conflict=verdict_conflict,
                left_confidence=left.confidence,
                right_confidence=right.confidence,
            )

            evidence_ids = (
                self._extract_evidence_ids(left)
                + self._extract_evidence_ids(right)
            )

            description = (
                f"Evaluator disagreement between "
                f"'{left.evaluator}' "
                f"({left.verdict}, {left.score:.2f}) "
                f"and "
                f"'{right.evaluator}' "
                f"({right.verdict}, {right.score:.2f})."
            )

            conflicts.append(
                ConsensusConflict(
                    conflict_id=str(uuid4()),
                    severity=severity,
                    description=description,
                    evaluators=[
                        left.evaluator,
                        right.evaluator,
                    ],
                    score_delta=round(
                        score_delta,
                        4,
                    ),
                    evidence_ids=evidence_ids,
                )
            )

        return conflicts

    @staticmethod
    def _verdicts_conflict(
        left: str,
        right: str,
    ) -> bool:

        failing = {
            "FAIL",
            "ERROR",
        }

        passing = {
            "PASS",
        }

        return (
            left in failing
            and right in passing
        ) or (
            right in failing
            and left in passing
        )

    @staticmethod
    def _conflict_severity(
        *,
        score_delta: float,
        verdict_conflict: bool,
        left_confidence: float,
        right_confidence: float,
    ) -> str:

        high_confidence = (
            left_confidence >= 0.80
            and right_confidence >= 0.80
        )

        if (
            verdict_conflict
            and score_delta >= 0.60
            and high_confidence
        ):
            return "critical"

        if verdict_conflict and high_confidence:
            return "high"

        if score_delta >= 0.60:
            return "high"

        if score_delta >= 0.40:
            return "medium"

        return "low"

    # ---------------------------------------------------------
    # Consensus score
    # ---------------------------------------------------------

    @staticmethod
    def _calculate_consensus_score(
        results: list[EvaluationResult],
    ) -> float:

        usable_results = [
            result
            for result in results
            if result.verdict != "ERROR"
        ]

        if not usable_results:
            return 0.0

        total_weight = sum(
            result.confidence
            for result in usable_results
        )

        if total_weight == 0:
            return 0.0

        weighted_score = sum(
            result.score * result.confidence
            for result in usable_results
        )

        return weighted_score / total_weight

    # ---------------------------------------------------------
    # Confidence
    # ---------------------------------------------------------

    @staticmethod
    def _calculate_confidence(
        results: list[EvaluationResult],
        conflicts: list[ConsensusConflict],
    ) -> float:

        if not results:
            return 0.0

        usable_results = [
            result
            for result in results
            if result.verdict != "ERROR"
        ]

        if not usable_results:
            return 0.0

        average_confidence = (
            sum(
                result.confidence
                for result in usable_results
            )
            / len(usable_results)
        )

        penalty = 0.0

        for conflict in conflicts:
            if conflict.severity == "critical":
                penalty += 0.20
            elif conflict.severity == "high":
                penalty += 0.12
            elif conflict.severity == "medium":
                penalty += 0.06
            else:
                penalty += 0.02

        return max(
            0.0,
            min(
                1.0,
                average_confidence - penalty,
            ),
        )

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    @staticmethod
    def _determine_status(
        results: list[EvaluationResult],
        conflicts: list[ConsensusConflict],
    ) -> str:

        if not results:
            return "INSUFFICIENT_EVIDENCE"

        usable_results = [
            result
            for result in results
            if result.verdict != "ERROR"
        ]

        if not usable_results:
            return "INSUFFICIENT_EVIDENCE"

        if not conflicts:
            return "CONSISTENT"

        if any(
            conflict.severity
            in {"critical", "high"}
            for conflict in conflicts
        ):
            return "MAJOR_CONFLICT"

        return "MINOR_CONFLICT"

    # ---------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------

    @staticmethod
    def _extract_evidence_ids(
        result: EvaluationResult,
    ) -> list[str]:

        return [
            evidence.evidence_id
            for evidence in result.evidence
        ]