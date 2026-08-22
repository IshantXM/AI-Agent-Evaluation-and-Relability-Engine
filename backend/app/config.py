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



def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


settings = Settings(
    database_url=os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/aegis",
    ),
    cors_origins=_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000")),
)
