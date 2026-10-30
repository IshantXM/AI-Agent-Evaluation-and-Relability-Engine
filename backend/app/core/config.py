 from __future__ import annotations

import os
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Path to .env (searches backend/.env first, then root .env)
BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent
ENV_FILES = (
    BACKEND_DIR / ".env",
    ROOT_DIR / ".env",
)


class Settings(BaseSettings):
    """Application-wide typed environment settings with validation."""
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server & Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/aegis"
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000"]
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Aegis Platform API"
    VERSION: str = "1.0.0"

    # Evaluation Model Provider
    AEGIS_JUDGE_API_KEY: str = ""
    AEGIS_JUDGE_MODEL: str = "gemini-1.5-flash"
    AEGIS_JUDGE_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    OPENAI_API_KEY: str = ""
    AEGIS_EVAL_MODEL: str = "gpt-4o"

    # Observability & LangSmith
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_PROJECT: str = "AEGIS-Multi-Agent-Platform"
    LANGCHAIN_API_KEY: str = ""

    @property
    def database_url(self) -> str:
        """Backward compatibility accessor."""
        return self.DATABASE_URL

    @property
    def cors_origins(self) -> tuple[str, ...]:
        """Backward compatibility accessor returning tuple of origins."""
        if isinstance(self.CORS_ORIGINS, list):
            return tuple(self.CORS_ORIGINS)
        return tuple(origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip())

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[str, List[str]]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
