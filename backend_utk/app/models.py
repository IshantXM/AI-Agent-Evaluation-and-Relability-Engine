from sqlalchemy import Column, Integer, String, JSON
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