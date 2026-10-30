from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, database

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.get("", response_model=List[Dict[str, Any]])
def list_evaluations(db: Session = Depends(database.get_db)):
    """List all evaluated reports in reverse chronological order."""
    evals = (
        db.query(models.EvaluationRecord)
        .order_by(models.EvaluationRecord.id.desc())
        .all()
    )
    return [
        {
            "id": e.id,
            "run_id": e.run_id,
            "agent_id": e.agent_id,
            "agent_version": e.agent_version,
            "overall_score": e.overall_score,
            "reliability_status": e.reliability_status,
            "evaluations": e.evaluations,
            "consensus": e.consensus,
            "adversarial_summary": e.adversarial_summary,
            "reliability": e.reliability,
            "report": e.report,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in evals
    ]


@router.get("/{run_id}", response_model=Dict[str, Any])
def get_evaluation(run_id: str, db: Session = Depends(database.get_db)):
    """Retrieve an evaluation record by run_id."""
    record = (
        db.query(models.EvaluationRecord)
        .filter(models.EvaluationRecord.run_id == run_id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation record for run_id '{run_id}' not found",
        )
    return {
        "id": record.id,
        "run_id": record.run_id,
        "agent_id": record.agent_id,
        "agent_version": record.agent_version,
        "overall_score": record.overall_score,
        "reliability_status": record.reliability_status,
        "evaluations": record.evaluations,
        "consensus": record.consensus,
        "adversarial_summary": record.adversarial_summary,
        "reliability": record.reliability,
        "report": record.report,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
