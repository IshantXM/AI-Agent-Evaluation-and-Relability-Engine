from __future__ import annotations

import pytest

from backend.app.evaluation.core.models import EvaluationResult
from backend.app.evaluation.judges.critic import CriticAgent
from backend.app.evaluation.judges.llm_judge import LLMJudge
from backend.app.evaluation.core.models import AgentTrace, TaskDefinition
from backend.app.evaluation.core.consensus_models import ConsensusResult


class StubJudge(LLMJudge):
    def _request(self, prompt: str) -> dict[str, object]:
        return {
            "verdict": "PASS",
            "score": 0.9,
            "confidence": 0.8,
            "summary": "The trace and evaluator evidence agree.",
        }


@pytest.mark.asyncio
async def test_llm_judge_reviews_evidence_without_creating_evaluator_result():
    trace = AgentTrace(
        run_id="judge-run",
        agent_id="agent",
        agent_version="1",
        task_id="task",
        task=TaskDefinition(input="Return 4", expected_output="4"),
        final_output="4",
        status="success",
    )
    evaluation = EvaluationResult(
        evaluation_id="evaluation-1",
        run_id=trace.run_id,
        evaluator="correctness",
        verdict="PASS",
        score=1.0,
        confidence=0.9,
        summary="Correct output.",
    )
    consensus: ConsensusResult = CriticAgent().evaluate([evaluation])

    review = await StubJudge(api_key="test").review(
        trace,
        [evaluation],
        consensus,
    )

    assert review is not None
    assert review.verdict == "PASS"
    assert review.score == 0.9
