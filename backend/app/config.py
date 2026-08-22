from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: tuple[str, ...]
    judge_api_key: str | None
    judge_model: str
    judge_base_url: str



def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


settings = Settings(
    database_url=os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/aegis",
    ),
    cors_origins=_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000")),
    judge_api_key=os.getenv("AEGIS_JUDGE_API_KEY"),
    judge_model=os.getenv("AEGIS_JUDGE_MODEL", "gemini-1.5-flash"),
    judge_base_url=os.getenv(
        "AEGIS_JUDGE_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai",
    ).rstrip("/"),
)
