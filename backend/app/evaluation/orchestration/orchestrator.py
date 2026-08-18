from __future__ import annotations

import asyncio
from uuid import uuid4

from ..core.base import BaseEvaluator
from ..core.models import AgentTrace, EvaluationResult
from ..core.registry import EvaluatorRegistry


class EvaluationOrchestrator:
    """
    Coordinates execution of registered Aegis evaluators.

    Responsibilities:
    - Resolve evaluators from the registry
    - Execute evaluators asynchronously
    - Isolate evaluator failures
    - Preserve deterministic result ordering
    - Support running all or selected evaluators
    """

    def __init__(self, registry: EvaluatorRegistry) -> None:
        self.registry = registry

    async def evaluate(
        self,
        trace: AgentTrace,
        evaluators: list[str] | None = None,
    ) -> list[EvaluationResult]:
        """
        Evaluate a trace using all registered evaluators or
        a selected subset.

        Args:
            trace: Agent execution trace.
            evaluators: Optional evaluator names.

        Returns:
            Evaluation results in deterministic evaluator order.
        """

        if evaluators is None:
            evaluator_names = self.registry.list()
        else:
            evaluator_names = evaluators

        # Resolve evaluators before execution so unknown names fail
        # deterministically instead of failing halfway through execution.
        resolved: list[tuple[str, BaseEvaluator]] = []

        for name in evaluator_names:
            resolved.append(
                (
                    name,
                    self.registry.get(name),
                )
            )

        async def run_evaluator(
            name: str,
            evaluator: BaseEvaluator,
        ) -> EvaluationResult:
            try:
                return await evaluator.evaluate(trace)

            except Exception as exc:
                return EvaluationResult(
                    evaluation_id=str(uuid4()),
                    run_id=trace.run_id,
                    evaluator=name,
                    verdict="ERROR",
                    score=0.0,
                    confidence=1.0,
                    findings=[],
                    evidence=[],
                    summary=(
                        f"Evaluator '{name}' failed during execution: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                    metadata={
                        "error_type": type(exc).__name__,
                        "orchestrator_error": True,
                    },
                )

        results = await asyncio.gather(
            *(
                run_evaluator(name, evaluator)
                for name, evaluator in resolved
            )
        )

        return list(results)