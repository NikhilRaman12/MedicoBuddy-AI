"""Centralised application configuration loaded from environment variables."""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — loaded from .env / environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "MedicoBuddy"
    app_env: str = "production"
    app_debug: bool = False
    app_log_level: str = "INFO"
    app_secret_key: str = Field(default="CHANGE_ME_RANDOM_SECRET_KEY_MIN_32_CHARS", min_length=16)

    # ── FastAPI ──────────────────────────────────────────────
    api_host: str = "0.0.0.0"  # noqa: S104
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list[str] = ["http://localhost:8501", "http://localhost:3000"]

    # ── LLM Provider (Groq API Primary) ────────────────────────
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model_name: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # ── Neo4j Knowledge Graph ────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # ── Primary Vector Store: Milvus ──────────────────────────
    vector_store_primary: str = "milvus"  # "milvus", "pgvector", "qdrant"
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "medicobuddy_evidence_qwen3"

    # ── Secondary Vector Store: PostgreSQL pgvector ──────────
    enable_pgvector: bool = True
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "medicobuddy"
    postgres_user: str = "medicobuddy"
    postgres_password: str = ""

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Embedding Model (Qwen3-Embedding-8B) ─────────────────
    embedding_model: str = "Qwen/Qwen3-Embedding-8B"
    embedding_dimension: int = 4096
    use_local_transformers: bool = False

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_requests_per_minute: int = 60

    # ── MCP / NCBI ───────────────────────────────────────────
    ncbi_api_key: str = ""
    ncbi_email: str = "clinician@medicobuddy.ai"
    ncbi_tool_name: str = "medicobuddy_graphrag"

    # ── Emergency Contacts ───────────────────────────────────
    emergency_contacts: dict[str, dict[str, str]] = Field(default_factory=lambda: {
        "IN": {"number": "112", "name": "Emergency Services India"},
        "US": {"number": "911", "name": "Emergency Services US"},
        "UK": {"number": "999", "name": "Emergency Services UK"},
        "EU": {"number": "112", "name": "Emergency Services EU"},
    })
    default_region: str = "IN"

    @field_validator("emergency_contacts", mode="before")
    @classmethod
    def parse_emergency_contacts(cls, v: Any) -> dict[str, dict[str, str]]:
        if isinstance(v, str):
            return json.loads(v)  # type: ignore[no-any-return]
        return v  # type: ignore[return-value]

    # ── Privacy & Regulatory ─────────────────────────────────
    enable_chat_history: bool = False
    data_retention_days: int = 30
    encrypt_at_rest: bool = True


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
