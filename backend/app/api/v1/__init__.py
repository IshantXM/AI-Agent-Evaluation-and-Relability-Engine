from __future__ import annotations

from fastapi import APIRouter
from app.api.v1.endpoints import traces, evaluations, scenarios

api_router = APIRouter()
api_router.include_router(traces.router)
api_router.include_router(evaluations.router)
api_router.include_router(scenarios.router)
