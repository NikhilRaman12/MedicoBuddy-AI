"""Centralised application configuration loaded from environment variables."""

from __future__ import annotations

import json
import os
import subprocess
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_git_sha() -> str:
    """Resolve current git commit SHA from env var, CI metadata, or git command."""
    # 1. Explicit env var (injected by CI or Dockerfile)
    sha = os.environ.get("GIT_COMMIT_SHA", "")
    if sha:
        return sha[:12]
    # 2. Try git command
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "dev"


GIT_COMMIT_SHA: str = _resolve_git_sha()


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
    # NOTE: Always 1 worker — in-memory embedding/index state is NOT worker-safe.
    api_workers: int = 1
    cors_origins: list[str] = ["http://localhost:8501", "http://localhost:3000"]

    # ── LLM Provider (Groq) ─────────────────────────────────
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model_name: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # ── Embedding Model ──────────────────────────────────────
    # When QWEN_EMBEDDING_ENDPOINT is set, use remote HF TEI endpoint.
    # When absent, fall back to local sentence-transformers (LOCAL_DEVELOPMENT_FALLBACK).
    embedding_model: str = "Qwen/Qwen3-Embedding-8B"
    embedding_dimension: int = 0  # 0 = derive from first model response
    qwen_embedding_endpoint: str = ""  # HF Inference Endpoint URL
    hf_token: str = ""  # HuggingFace API token
    embedding_timeout_seconds: int = 30
    use_local_transformers: bool = False  # Force local sentence-transformers

    # ── PostgreSQL / pgvector ─────────────────────────────────
    # Provide POSTGRES_DSN as a full DSN to override individual host/port settings.
    postgres_dsn: str = ""  # e.g. postgresql+asyncpg://user:pw@host:5432/db
    enable_pgvector: bool = True
    # Legacy individual fields kept for backward compat (used when postgres_dsn is empty)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "medicobuddy"
    postgres_user: str = "medicobuddy"
    postgres_password: str = ""

    def get_postgres_dsn(self) -> str:
        """Return the effective PostgreSQL DSN."""
        if self.postgres_dsn:
            return self.postgres_dsn
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Milvus ───────────────────────────────────────────────
    enable_milvus: bool = False  # Requires MILVUS_URI to be set
    milvus_uri: str = ""  # e.g. https://....zilliz.cloud:443
    milvus_token: str = ""  # Zilliz Cloud / Milvus API token
    milvus_collection: str = "medicobuddy_evidence"
    # Legacy host/port kept for local Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    def get_milvus_uri(self) -> str:
        """Return the effective Milvus URI."""
        if self.milvus_uri:
            return self.milvus_uri
        return f"http://{self.milvus_host}:{self.milvus_port}"

    # ── Neo4j Knowledge Graph ────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
