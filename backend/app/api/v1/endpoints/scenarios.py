from __future__ import annotations

from fastapi import APIRouter
from app.schemas.trace import ScenarioGenerationRequest, ScenarioGenerationResponse
from app.services.scenario_service import generate_adversarial_scenarios

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.post("/generate", response_model=ScenarioGenerationResponse)
async def generate_scenarios(req: ScenarioGenerationRequest):
    """
    Generate realistic multi-step tasks, adversarial prompt injections,
    destructive action probes, and tool-loop triggers based on agent tools and domain.
    """
    result = generate_adversarial_scenarios(
        domain=req.domain,
        tools=req.tools,
        num_scenarios=req.num_scenarios or 4,
    )
    return result
