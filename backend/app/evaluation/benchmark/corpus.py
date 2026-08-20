from __future__ import annotations

import json
from pathlib import Path

from .models import BenchmarkCase


class BenchmarkCorpus:
    """
    Loads and validates the benchmark ground-truth corpus.

    Responsibilities:
    - load benchmark cases from JSON
    - validate cases through Pydantic
    - provide deterministic case lookup
    - prevent duplicate case identifiers

    Non-responsibilities:
    - executing evaluations
    - calculating benchmark metrics
    - modifying traces
    """

    def __init__(
        self,
        cases: list[BenchmarkCase],
    ) -> None:
        self._cases = tuple(cases)

        case_ids = [case.case_id for case in self._cases]

        if len(case_ids) != len(set(case_ids)):
            raise ValueError(
                "Benchmark corpus contains duplicate case_id values."
            )

    @classmethod
    def from_file(
        cls,
        path: str | Path,
    ) -> BenchmarkCorpus:
        """
        Load benchmark cases from a JSON file.
        """

        corpus_path = Path(path)

        if not corpus_path.exists():
            raise FileNotFoundError(
                f"Benchmark corpus not found: {corpus_path}"
            )

        if not corpus_path.is_file():
            raise ValueError(
                f"Benchmark corpus path is not a file: {corpus_path}"
            )

        try:
            payload = json.loads(
                corpus_path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid benchmark corpus JSON: {corpus_path}"
            ) from exc

        if not isinstance(payload, list):
            raise ValueError(
                "Benchmark corpus root must be a JSON array."
            )

        cases = [
            BenchmarkCase.model_validate(item)
            for item in payload
        ]

        return cls(cases)

    @property
    def cases(self) -> tuple[BenchmarkCase, ...]:
        """
        Return benchmark cases in deterministic corpus order.
        """

        return self._cases

    def __len__(self) -> int:
        return len(self._cases)

    def get(
        self,
        case_id: str,
    ) -> BenchmarkCase:
        """
        Retrieve a benchmark case by identifier.
        """

        for case in self._cases:
            if case.case_id == case_id:
                return case

        raise KeyError(
            f"Unknown benchmark case: {case_id}"
        )

    def select(
        self,
        case_ids: list[str] | None = None,
    ) -> list[BenchmarkCase]:
        """
        Select benchmark cases.

        If case_ids is omitted, all cases are returned.

        Explicit selection preserves the order requested by
        the caller.
        """

        if case_ids is None:
            return list(self._cases)

        return [
            self.get(case_id)
            for case_id in case_ids
        ]