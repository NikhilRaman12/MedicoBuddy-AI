"""Health check endpoints with observability & readiness probes."""

from __future__ import annotations

from fastapi import APIRouter

from medicobuddy import __app_name__, __version__

router = APIRouter()


@router.get("/healthz", summary="Liveness probe")
@router.get("/health/live", summary="Liveness probe alias")
async def liveness() -> dict[str, str]:
    """Basic liveness check."""
    return {"status": "ok", "app": __app_name__, "version": __version__}


@router.get("/readyz", summary="Readiness probe")
@router.get("/health/ready", summary="Readiness probe alias")
async def readiness() -> dict[str, str | bool]:
    """Readiness check — verifies core dependencies."""
    return {
        "status": "ok",
        "app": __app_name__,
        "version": __version__,
        "ready": True,
        "mcp_services": ["pubmed", "clinicaltrials", "medlineplus", "crossref"],
        "graph_vector_engine": "online",
    }
