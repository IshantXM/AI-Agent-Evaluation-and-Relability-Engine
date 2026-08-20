from __future__ import annotations

from dataclasses import dataclass

from ..adversarial.aggregator import AdversarialAggregator
from ..adversarial.engine import AdversarialEngine
from ..adversarial.models import (
    AdversarialResult,
    AdversarialScenario,
    AdversarialSummary,
)
from ..agents.critic import CriticAgent
from ..core.consensus_models import ConsensusResult
from ..core.models import AgentTrace, EvaluationResult
from ..core.report_models import ReliabilityReport
from ..reliability.assessor import ReliabilityAssessor
from ..reliability.models import ReliabilityAssessment
from .orchestrator import EvaluationOrchestrator
from .report_builder import ReportBuilder


@dataclass
class EvaluationRunResult:
    """
    Complete evaluation artifact for a single agent execution.

    The result intentionally preserves every major stage of the
    evaluation pipeline instead of exposing only the final report.

    Pipeline:

        AgentTrace
            |
            v
        Standard Evaluators
            |
            v
        Consensus
            |
            +------------------+
            |                  |
            v                  v
        Standard          Adversarial
        Evaluation        Evaluation
            |                  |
            |                  v
            |          Adversarial Summary
            |                  |
            +--------+---------+
                     |
                     v
             Reliability Assessment
                     |
                     v
              Reliability Report
    """

    run_id: str

    evaluations: list[EvaluationResult]

    consensus: ConsensusResult

    adversarial_results: list[AdversarialResult]

    adversarial_summary: AdversarialSummary

    reliability: ReliabilityAssessment

    report: ReliabilityReport


class EvaluationService:
    """
    Production composition layer for the complete evaluation pipeline.

    Responsibilities
    ----------------
    1. Execute standard evaluators.
    2. Produce confidence-weighted evaluator consensus.
    3. Execute configured adversarial scenarios.
    4. Aggregate adversarial resilience.
    5. Calculate evaluation coverage.
    6. Produce a unified reliability assessment.
    7. Build the externally persisted reliability report.

    The service itself contains no evaluator logic and no model
    inference logic. It composes independently testable components.

    The service is deterministic with respect to its dependencies
    and has no mutable evaluation state.
    """

    SUPPORTED_EVALUATORS: frozenset[str] = frozenset(
        {
            "correctness",
            "grounding",
            "tool_use",
            "safety",
            "robustness",
            "efficiency",
        }
    )

    def __init__(
        self,
        orchestrator: EvaluationOrchestrator,
        critic: CriticAgent | None = None,
        report_builder: ReportBuilder | None = None,
        adversarial_engine: AdversarialEngine | None = None,
        adversarial_aggregator: AdversarialAggregator | None = None,
        reliability_assessor: ReliabilityAssessor | None = None,
    ) -> None:
        """
        Initialize the evaluation composition layer.

        Dependencies are injectable so individual pipeline stages can
        be replaced with deterministic test doubles when necessary.
        """

        self.orchestrator = orchestrator

        self.critic = critic or CriticAgent()

        self.report_builder = (
            report_builder
            or ReportBuilder()
        )

        self.adversarial_engine = (
            adversarial_engine
            or AdversarialEngine()
        )

        self.adversarial_aggregator = (
            adversarial_aggregator
            or AdversarialAggregator()
        )

        self.reliability_assessor = (
            reliability_assessor
            or ReliabilityAssessor()
        )

    async def evaluate(
        self,
        trace: AgentTrace,
        evaluators: list[str] | None = None,
        adversarial_scenarios: list[AdversarialScenario] | None = None,
        previous_score: float | None = None,
        previous_version: str | None = None,
    ) -> EvaluationRunResult:
        """
        Execute the complete reliability evaluation pipeline.

        Parameters
        ----------
        trace:
            Immutable execution trace of the agent run.

        evaluators:
            Optional subset of standard evaluators to execute.

        adversarial_scenarios:
            Optional adversarial scenarios. If omitted, the adversarial
            stage executes with zero scenarios rather than inventing
            scenarios implicitly.

        previous_score:
            Previous reliability/report score used for regression
            analysis.

        previous_version:
            Previous agent version associated with previous_score.

        Returns
        -------
        EvaluationRunResult
            Complete evaluation artifact containing standard
            evaluations, consensus, adversarial analysis,
            reliability assessment, and final report.
        """

        # ========================================================
        # Stage 1: Standard evaluation
        # ========================================================

        evaluations = await self.orchestrator.evaluate(
            trace=trace,
            evaluators=evaluators,
        )

        # ========================================================
        # Stage 2: Cross-evaluator consensus
        # ========================================================

        consensus = self.critic.evaluate(
            evaluations
        )

        # ========================================================
        # Stage 3: Adversarial evaluation
        # ========================================================

        scenarios = adversarial_scenarios or []

        adversarial_results = (
            self.adversarial_engine.evaluate(
                trace=trace,
                scenarios=scenarios,
            )
        )

        # ========================================================
        # Stage 4: Adversarial aggregation
        # ========================================================

        adversarial_summary = (
            self.adversarial_aggregator.aggregate(
                adversarial_results
            )
        )

        # ========================================================
        # Stage 5: Evaluation coverage
        # ========================================================

        evaluation_coverage = (
            self._calculate_evaluation_coverage(
                evaluations
            )
        )

        # ========================================================
        # Stage 6: Unified reliability assessment
        # ========================================================

        reliability = self.reliability_assessor.assess(
            consensus=consensus,
            adversarial=adversarial_summary,
            evaluation_coverage=evaluation_coverage,
        )

        # ========================================================
        # Stage 7: External reliability report
        # ========================================================

        report = self.report_builder.build(
            run_id=trace.run_id,
            agent_id=trace.agent_id,
            agent_version=trace.agent_version,
            results=evaluations,
            previous_score=previous_score,
            previous_version=previous_version,
        )

        # ========================================================
        # Final pipeline artifact
        # ========================================================

        return EvaluationRunResult(
            run_id=trace.run_id,
            evaluations=evaluations,
            consensus=consensus,
            adversarial_results=adversarial_results,
            adversarial_summary=adversarial_summary,
            reliability=reliability,
            report=report,
        )

    # ============================================================
    # Evaluation Coverage
    # ============================================================

    @classmethod
    def _calculate_evaluation_coverage(
        cls,
        evaluations: list[EvaluationResult],
    ) -> float:
        """
        Calculate standard evaluation coverage.

        Coverage measures how many supported evaluation dimensions
        were actually executed.

        It is deliberately independent of evaluator score.

        Examples
        --------
        6 supported evaluators executed -> 1.0
        3 supported evaluators executed -> 0.5
        1 supported evaluator executed  -> 1/6
        0 evaluators executed            -> 0.0

        Unknown/custom evaluators do not increase coverage because
        they cannot be mapped reliably to the canonical evaluation
        dimensions.
        """

        if not evaluations:
            return 0.0

        evaluated = {
            evaluation.evaluator
            for evaluation in evaluations
            if evaluation.evaluator
            in cls.SUPPORTED_EVALUATORS
        }

        return (
            len(evaluated)
            / len(cls.SUPPORTED_EVALUATORS)
        )