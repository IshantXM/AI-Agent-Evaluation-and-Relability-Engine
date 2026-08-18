from __future__ import annotations

from uuid import uuid4

from ..core.models import EvaluationResult
from ..core.report_models import (
    DimensionScore,
    Recommendation,
    Regression,
    ReliabilityReport,
    ReportFailure,
    RootCause,
)


class ReportBuilder:
    """
    Aggregates evaluator results into a standardized
    Aegis ReliabilityReport.

    The report is coverage-aware:
    every required reliability dimension contributes to
    the aggregate score. An unevaluated dimension receives
    score=0.0 and status=NOT_EVALUATED.

    This prevents an agent from appearing perfectly reliable
    simply because some dimensions were never evaluated.
    """

    DIMENSIONS = (
        "correctness",
        "grounding",
        "tool_use",
        "safety",
        "robustness",
        "efficiency",
    )

    def build(
        self,
        *,
        run_id: str,
        agent_id: str,
        agent_version: str,
        results: list[EvaluationResult],
        previous_score: float | None = None,
        previous_version: str | None = None,
    ) -> ReliabilityReport:

        # --------------------------------------------------
        # Index evaluator results
        # --------------------------------------------------

        by_evaluator = {
            result.evaluator: result
            for result in results
        }

        dimensions: dict[str, DimensionScore] = {}

        # --------------------------------------------------
        # Build all required dimensions
        # --------------------------------------------------

        for dimension in self.DIMENSIONS:
            result = by_evaluator.get(dimension)

            # Dimension was not evaluated at all.
            if result is None:
                dimensions[dimension] = DimensionScore(
                    score=0.0,
                    confidence=0.0,
                    status="NOT_EVALUATED",
                    evaluation_ids=[],
                )
                continue

            # Evaluator crashed / returned an orchestration error.
            # Do not classify this as PASS or FAIL.
            if result.verdict == "ERROR":
                dimensions[dimension] = DimensionScore(
                    score=0.0,
                    confidence=0.0,
                    status="NOT_EVALUATED",
                    evaluation_ids=[result.evaluation_id],
                )
                continue

            # Normal evaluator result.
            dimensions[dimension] = DimensionScore(
                score=result.score,
                confidence=result.confidence,
                status=result.verdict,
                evaluation_ids=[result.evaluation_id],
            )

        # --------------------------------------------------
        # Coverage-aware overall score
        # --------------------------------------------------
        #
        # IMPORTANT:
        #
        # We average across ALL required dimensions, not
        # only dimensions that happened to be evaluated.
        #
        # Therefore:
        #
        #   5 passing dimensions
        #   1 unevaluated dimension
        #
        # produces:
        #
        #   5 / 6 = 0.8333
        #
        # instead of:
        #
        #   5 / 5 = 1.0
        #
        # This prevents missing evaluation coverage from
        # artificially producing a perfect reliability score.
        # --------------------------------------------------

        overall_score = sum(
            dimensions[dimension].score
            for dimension in self.DIMENSIONS
        ) / len(self.DIMENSIONS)

        # Confidence is based only on dimensions that actually
        # produced an evaluation result.
        evaluated_dimensions = [
            dimensions[dimension]
            for dimension in self.DIMENSIONS
            if dimensions[dimension].status != "NOT_EVALUATED"
        ]

        if evaluated_dimensions:
            confidence = sum(
                dimension.confidence
                for dimension in evaluated_dimensions
            ) / len(evaluated_dimensions)
        else:
            confidence = 0.0

        # --------------------------------------------------
        # Failures
        # --------------------------------------------------

        failures = self._build_failures(results)

        # --------------------------------------------------
        # Root causes
        # --------------------------------------------------

        root_causes = self._build_root_causes(results)

        # --------------------------------------------------
        # Recommendations
        # --------------------------------------------------

        recommendations = self._build_recommendations(
            failures,
            results,
        )

        # --------------------------------------------------
        # Regression
        # --------------------------------------------------

        regression = self._build_regression(
            current_score=overall_score,
            previous_score=previous_score,
            previous_version=previous_version,
        )

        # --------------------------------------------------
        # Final report
        # --------------------------------------------------

        return ReliabilityReport(
            report_id=str(uuid4()),
            run_id=run_id,
            agent_id=agent_id,
            agent_version=agent_version,
            overall_score=round(overall_score, 4),
            confidence=round(confidence, 4),
            dimensions=dimensions,
            failures=failures,
            root_causes=root_causes,
            recommendations=recommendations,
            regression=regression,
            metadata={
                "evaluators_run": len(results),
                "evaluated_dimensions": len(evaluated_dimensions),
                "total_dimensions": len(self.DIMENSIONS),
                "evaluation_coverage": round(
                    len(evaluated_dimensions) / len(self.DIMENSIONS),
                    4,
                ),
            },
        )

    # ======================================================
    # Failures
    # ======================================================

    def _build_failures(
        self,
        results: list[EvaluationResult],
    ) -> list[ReportFailure]:

        failures: list[ReportFailure] = []

        for result in results:
            for finding in result.findings:

                if finding.severity == "info":
                    continue

                failures.append(
                    ReportFailure(
                        failure_id=finding.finding_id,
                        severity=finding.severity,
                        description=finding.description,
                        evaluator=result.evaluator,
                        event_ids=finding.event_ids,
                    )
                )

        return failures

    # ======================================================
    # Root Causes
    # ======================================================

    def _build_root_causes(
        self,
        results: list[EvaluationResult],
    ) -> list[RootCause]:

        root_causes: list[RootCause] = []

        category_map = {
            "correctness": "reasoning",
            "grounding": "grounding",
            "tool_use": "tool_execution",
            "safety": "safety",
            "robustness": "robustness",
            "efficiency": "efficiency",
        }

        for result in results:

            if result.verdict not in {
                "FAIL",
                "PARTIAL",
                "ERROR",
            }:
                continue

            category = category_map.get(
                result.evaluator,
                "unknown",
            )

            for finding in result.findings:

                root_causes.append(
                    RootCause(
                        cause_id=str(uuid4()),
                        category=category,
                        description=finding.description,
                        confidence=result.confidence,
                        event_ids=finding.event_ids,
                    )
                )

        return root_causes

    # ======================================================
    # Recommendations
    # ======================================================

    def _build_recommendations(
        self,
        failures: list[ReportFailure],
        results: list[EvaluationResult],
    ) -> list[Recommendation]:

        recommendations: list[Recommendation] = []

        for failure in failures:

            recommendations.append(
                Recommendation(
                    recommendation_id=str(uuid4()),
                    description=(
                        f"Investigate and remediate: "
                        f"{failure.description}"
                    ),
                    priority=failure.severity,
                    related_failure_ids=[
                        failure.failure_id
                    ],
                )
            )

        return recommendations

    # ======================================================
    # Regression
    # ======================================================

    def _build_regression(
        self,
        *,
        current_score: float,
        previous_score: float | None,
        previous_version: str | None,
    ) -> Regression:

        # No previous score means this is the baseline.
        if previous_score is None:
            return Regression(
                status="BASELINE",
                previous_score=None,
                score_delta=None,
                previous_version=previous_version,
            )

        delta = round(
            current_score - previous_score,
            4,
        )

        if delta > 0:
            status = "IMPROVED"
        elif delta < 0:
            status = "REGRESSED"
        else:
            status = "UNCHANGED"

        return Regression(
            status=status,
            previous_score=previous_score,
            score_delta=delta,
            previous_version=previous_version,
        )