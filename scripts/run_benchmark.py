from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.evaluation.benchmark import BenchmarkCorpus, BenchmarkRunner
from backend.app.evaluation.orchestration import EvaluationPipeline
from backend.app.evaluation_bootstrap import get_evaluation_orchestrator


async def main(corpus_path: Path, trace_directory: Path) -> None:
    corpus = BenchmarkCorpus.from_file(corpus_path)
    pipeline = EvaluationPipeline(get_evaluation_orchestrator())
    results = await BenchmarkRunner(
        pipeline=pipeline,
        trace_directory=trace_directory,
    ).run(corpus)
    print(json.dumps([result.model_dump(mode="json") for result in results], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the benchmark corpus.")
    parser.add_argument("--corpus", type=Path, default=Path("backend/tests/fixtures/benchmarks/benchmark_cases.json"))
    parser.add_argument("--traces", type=Path, default=Path("backend/tests/fixtures/traces"))
    args = parser.parse_args()
    asyncio.run(main(args.corpus, args.traces))
