import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Defaults to a local sqlite file so anyone can `uvicorn app.main:app`
# with zero setup. Set DATABASE_URL to a postgres DSN when you're
# ready to move to Step 3 of the direction doc, e.g.:
#   postgresql://aegis:aegis@localhost:5432/aegis
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aegis_traces.db")

connect_args = (
    {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
