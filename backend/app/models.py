from sqlalchemy import Column, Integer, String, JSON, Float
from .database import Base


class TraceRecord(Base):
    __tablename__ = "traces"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True)
    agent_id = Column(String, index=True)
    agent_version = Column(String)
    task_id = Column(String, index=True)
    task = Column(JSON)
    events = Column(JSON)
    metrics = Column(JSON)
    final_output = Column(String, nullable=True)
    status = Column(String)


class EvaluationRecord(Base):
    """
    Persists the full output of the evaluation engine for a single
    run_id: per-evaluator results, consensus, adversarial summary,
    reliability assessment, and the final report.

    Stored as JSON blobs rather than fully normalized tables on
    purpose -- for a hackathon timeline this gets Milestone 2 working
    today. Normalize into `evaluations` / `findings` / `failures`
    tables later (Step 3 in the direction doc) once the shape has
    stabilized and you actually need to query into it (e.g. "all
    FAIL verdicts for evaluator=safety across runs").
    """

    __tablename__ = "evaluation_records"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True)
    agent_id = Column(String, index=True)
    agent_version = Column(String, index=True)

    overall_score = Column(Float, nullable=True)
    reliability_status = Column(String, nullable=True)

    evaluations = Column(JSON)          # list[EvaluationResult] as dicts
    consensus = Column(JSON)            # ConsensusResult as dict
    adversarial_summary = Column(JSON)  # AdversarialSummary as dict
    reliability = Column(JSON)          # ReliabilityAssessment as dict
    report = Column(JSON)               # ReliabilityReport as dict
