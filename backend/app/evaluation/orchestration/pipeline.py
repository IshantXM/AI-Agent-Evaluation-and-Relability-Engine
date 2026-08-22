from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..judges.critic import CriticAgent
from ..core.models import AgentTrace, EvaluationResult
from ..core.consensus_models import ConsensusResult
from .orchestrator import EvaluationOrchestrator


@dataclass
class EvaluationPipelineResult:
    """
    Complete evaluation output for a single agent run.

    Contains:
    - individual evaluator results
    - cross-evaluator consensus
    """

    run_id: str
    evaluations: list[EvaluationResult]
    consensus: ConsensusResult

    @property
    def score(self) -> float:
        return self.consensus.consensus_score

    @property
    def confidence(self) -> float:
        return self.consensus.confidence


class EvaluationPipeline:
    """
    High-level evaluation pipeline.

    Execution flow:

        AgentTrace
            ↓
        EvaluationOrchestrator
            ↓
        Individual EvaluationResults
            ↓
        CriticAgent
            ↓
        ConsensusResult

    The pipeline deliberately keeps evaluator execution and
    consensus analysis separate.

    This allows:
    - individual evaluator failures to be isolated
    - evaluator results to remain independently inspectable
    - the critic to reason over the complete evaluation set
    """

    def __init__(
        self,
        orchestrator: EvaluationOrchestrator,
        critic: CriticAgent | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.critic = critic or CriticAgent()

    async def evaluate(
        self,
        trace: AgentTrace,
        evaluators: list[str] | None = None,
    ) -> EvaluationPipelineResult:
        """
        Evaluate one agent trace and produce consensus.

        Args:
            trace:
                Agent execution trace.

            evaluators:
                Optional list of evaluator names.
                If omitted, all registered evaluators are executed.

        Returns:
            EvaluationPipelineResult
        """

        evaluation_results = await self.orchestrator.evaluate(
            trace=trace,
            evaluators=evaluators,
        )

        consensus = self.critic.evaluate(
            evaluation_results
        )

        return EvaluationPipelineResult(
            run_id=trace.run_id,
            evaluations=evaluation_results,
            consensus=consensus,
        )