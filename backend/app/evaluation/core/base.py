from abc import ABC, abstractmethod

from .models import AgentTrace, EvaluationResult


class BaseEvaluator(ABC):
    """
    Base interface implemented by every Aegis evaluator.

    Every evaluator receives an AgentTrace and produces
    a standardized EvaluationResult.
    """

    name: str = "base"

    @abstractmethod
    async def evaluate(self, trace: AgentTrace) -> EvaluationResult:
        """
        Evaluate an agent execution trace.

        Args:
            trace: Complete execution trace of the agent.

        Returns:
            Standardized evaluation result.
        """
        raise NotImplementedError