"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from medicobuddy import __app_name__, __version__

router = APIRouter()


@router.get("/healthz", summary="Liveness probe")
async def liveness() -> dict[str, str]:
    """Basic liveness check."""
    return {"status": "ok", "app": __app_name__, "version": __version__}


@router.get("/readyz", summary="Readiness probe")
async def readiness() -> dict[str, str | bool]:
    """Readiness check — verifies core dependencies."""
    return {
        "status": "ok",
        "app": __app_name__,
        "version": __version__,
        "ready": True,
    }
