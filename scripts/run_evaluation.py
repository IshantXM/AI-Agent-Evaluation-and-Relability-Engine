from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.evaluation_bootstrap import build_agent_trace, evaluate_trace


async def main(path: Path) -> None:
    trace = build_agent_trace(json.loads(path.read_text(encoding="utf-8")))
    result = await evaluate_trace(trace)
    print(json.dumps(result.report.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate one trace and print its report.")
    parser.add_argument("trace", type=Path)
    asyncio.run(main(parser.parse_args().trace))
