import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file if present
load_dotenv()

# Defaults to a local sqlite file if DATABASE_URL is not set
# Example Postgres URL: postgresql://user:password@localhost:5432/aegis_db
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aegis_traces.db")

# Fix legacy postgres:// URI scheme if provided by providers like Heroku/Neon
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

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
