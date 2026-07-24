"""Consent management endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ConsentRequest(BaseModel):
    """Consent submission."""

    consent_type: str  # "chat_history", "data_processing"
    granted: bool


class ConsentResponse(BaseModel):
    """Consent confirmation."""

    message: str
    consent_type: str
    granted: bool


@router.post("/consent", response_model=ConsentResponse, summary="Submit consent preference")
async def submit_consent(request: ConsentRequest) -> ConsentResponse:
    """Record user consent preference.

    In production, this persists to PostgreSQL with timestamps and audit trail.
    """
    # Production: store in PostgreSQL with audit logging
    return ConsentResponse(
        message="Consent preference recorded",
        consent_type=request.consent_type,
        granted=request.granted,
    )
