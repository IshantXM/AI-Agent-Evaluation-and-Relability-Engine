from pathlib import Path

import pytest

from backend.app.evaluation.benchmark.corpus import BenchmarkCorpus


BENCHMARK_PATH = (
    Path(__file__).parents[1]
    / "fixtures"
    / "benchmarks"
    / "benchmark_cases.json"
)


def test_corpus_loads_all_cases() -> None:
    corpus = BenchmarkCorpus.from_file(BENCHMARK_PATH)

    assert len(corpus) == 10


def test_corpus_case_ids_are_unique() -> None:
    corpus = BenchmarkCorpus.from_file(BENCHMARK_PATH)

    case_ids = [
        case.case_id
        for case in corpus.cases
    ]

    assert len(case_ids) == len(set(case_ids))


def test_corpus_lookup_returns_expected_case() -> None:
    corpus = BenchmarkCorpus.from_file(BENCHMARK_PATH)

    case = corpus.get("correctness_correct")

    assert case.category == "correctness"
    assert case.trace_file == "correct_trace.json"


def test_corpus_unknown_case_raises() -> None:
    corpus = BenchmarkCorpus.from_file(BENCHMARK_PATH)

    with pytest.raises(KeyError):
        corpus.get("does_not_exist")


def test_corpus_selection_preserves_requested_order() -> None:
    corpus = BenchmarkCorpus.from_file(BENCHMARK_PATH)

    selected = corpus.select(
        [
            "safety_unsafe",
            "correctness_correct",
            "tool_failure",
        ]
    )

    assert [
        case.case_id
        for case in selected
    ] == [
        "safety_unsafe",
        "correctness_correct",
        "tool_failure",
    ]


def test_corpus_all_selection_is_deterministic() -> None:
    corpus = BenchmarkCorpus.from_file(BENCHMARK_PATH)

    first = [
        case.case_id
        for case in corpus.select()
    ]

    second = [
        case.case_id
        for case in corpus.select()
    ]

    assert first == second