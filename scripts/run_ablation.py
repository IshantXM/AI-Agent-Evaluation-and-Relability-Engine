from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.evaluation.ablation import AblationRunner
from backend.app.evaluation_bootstrap import build_agent_trace, get_evaluation_orchestrator


async def main(trace_path: Path, trials: int) -> None:
    trace = build_agent_trace(json.loads(trace_path.read_text(encoding="utf-8")))
    report = await AblationRunner(get_evaluation_orchestrator()).run(trace, trials=trials)
    print(json.dumps(report.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a leave-one-evaluator-out ablation.")
    parser.add_argument("trace", type=Path)
    parser.add_argument("--trials", type=int, default=1)
    args = parser.parse_args()
    asyncio.run(main(args.trace, args.trials))
