"""FastAPI dependency injection module."""

from __future__ import annotations

from fastapi import Request

from medicobuddy.services import RuntimeServices


def get_services(request: Request) -> RuntimeServices:
    """Extract RuntimeServices from FastAPI app state."""
    services = getattr(request.app.state, "services", None)
    if services is None:
        raise RuntimeError("RuntimeServices not initialized on app state")
    return services
