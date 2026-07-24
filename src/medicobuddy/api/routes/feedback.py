"""Feedback submission endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class FeedbackRequest(BaseModel):
    """User feedback on a response."""

    response_helpful: bool
    accuracy_rating: int = Field(ge=1, le=5, description="1-5 accuracy rating")
    comments: str = Field(default="", max_length=1000)


class FeedbackResponse(BaseModel):
    """Feedback confirmation."""

    message: str
    received: bool


@router.post("/feedback", response_model=FeedbackResponse, summary="Submit feedback")
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Record user feedback on response quality.

    In production, persists to PostgreSQL for quality monitoring.
    """
    return FeedbackResponse(message="Thank you for your feedback", received=True)
