from .base import BaseEvaluator


class EvaluatorRegistry:
    """
    Registry for dynamically discovering and retrieving
    Aegis evaluators.
    """

    def __init__(self) -> None:
        self._evaluators: dict[str, BaseEvaluator] = {}

    def register(self, evaluator: BaseEvaluator) -> None:
        """
        Register an evaluator by its unique name.
        """

        if evaluator.name in self._evaluators:
            raise ValueError(
                f"Evaluator '{evaluator.name}' is already registered."
            )

        self._evaluators[evaluator.name] = evaluator

    def get(self, name: str) -> BaseEvaluator:
        """
        Retrieve an evaluator by name.
        """

        try:
            return self._evaluators[name]
        except KeyError:
            raise KeyError(
                f"Evaluator '{name}' is not registered."
            ) from None

    def list(self) -> list[str]:
        """
        Return names of all registered evaluators.
        """

        return sorted(self._evaluators.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._evaluators