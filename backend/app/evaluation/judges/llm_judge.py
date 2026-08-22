from __future__ import annotations

import asyncio
import json
import urllib.request
from typing import Any

from pydantic import BaseModel

from ..core.consensus_models import ConsensusResult
from ..core.models import AgentTrace, EvaluationResult
from ...config import Settings


class LLMJudgeReview(BaseModel):
    """Model-based review of evaluator evidence, not an evaluator dimension."""

    verdict: str
    score: float
    confidence: float
    summary: str
    finding: str | None = None


class LLMJudge:
    """Optional model review layer for evaluator consensus and reliability."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = (
            base_url
            or "https://generativelanguage.googleapis.com/v1beta/openai"
        ).rstrip("/")
        self.model = model or "gemini-1.5-flash"
        self.timeout_seconds = timeout_seconds

    async def review(
        self,
        trace: AgentTrace,
        evaluations: list[EvaluationResult],
        consensus: ConsensusResult,
    ) -> LLMJudgeReview | None:
        prompt = self._build_prompt(trace, evaluations, consensus)
        try:
            payload = await asyncio.to_thread(self._request, prompt)
            verdict = str(payload.get("verdict", "PARTIAL")).upper()
            if verdict not in {"PASS", "FAIL", "PARTIAL"}:
                verdict = "PARTIAL"
            score = self._bounded_float(payload.get("score"), 0.5)
            confidence = self._bounded_float(payload.get("confidence"), 0.5)
            return LLMJudgeReview(
                verdict=verdict,
                score=score,
                confidence=confidence,
                summary=str(payload.get("summary") or "LLM review completed."),
                finding=str(payload["finding"]) if payload.get("finding") else None,
            )
        except Exception as exc:
            return LLMJudgeReview(
                verdict="ERROR",
                score=0.0,
                confidence=0.0,
                summary=f"LLM review unavailable: {type(exc).__name__}: {exc}",
            )

    def _request(self, prompt: str) -> dict[str, Any]:
        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an impartial AI-agent evaluator. "
                            "Return only JSON with keys verdict, score, confidence, summary, finding. "
                            "verdict must be PASS, PARTIAL, or FAIL; score and confidence are 0 to 1."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        content = response_data["choices"][0]["message"]["content"]
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError("Judge response was not a JSON object")
        return result

    @staticmethod
    def _build_prompt(
        trace: AgentTrace,
        evaluations: list[EvaluationResult],
        consensus: ConsensusResult,
    ) -> str:
        events = [
            {
                "type": event.event_type,
                "status": event.status,
                "payload": event.payload,
            }
            for event in trace.events
        ]
        return json.dumps(
            {
                "task": trace.task.model_dump(mode="json"),
                "final_output": trace.final_output,
                "run_status": trace.status,
                "events": events,
                "evaluator_results": [
                    result.model_dump(mode="json") for result in evaluations
                ],
                "deterministic_consensus": consensus.model_dump(mode="json"),
            },
            ensure_ascii=True,
        )

    @staticmethod
    def _bounded_float(value: Any, default: float) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return default


def configured_llm_judge(settings: Settings) -> LLMJudge | None:
    if not settings.judge_api_key:
        return None
    return LLMJudge(
        api_key=settings.judge_api_key,
        base_url=settings.judge_base_url,
        model=settings.judge_model,
    )
