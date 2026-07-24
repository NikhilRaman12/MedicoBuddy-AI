"""Chat endpoint — main conversation API."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from medicobuddy.models.response import MedicoBuddyResponse
from medicobuddy.models.symptom import TriageOutcome
from medicobuddy.models.user_context import AgeRange, PregnancyStatus, UserContext
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str = Field(min_length=1, max_length=2000, description="User message")
    age_range: str = Field(default="unknown")
    pregnancy_status: str = Field(default="unknown")
    is_immunocompromised: bool | None = None
    chronic_conditions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    region: str = Field(default="IN")
    consent_given: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Chat API response."""

    triage_outcome: str
    urgency_summary: str
    user_report_summary: str
    safe_comfort_steps: list[str]
    ayurveda_perspectives: list[dict[str, str]]
    things_to_avoid: list[str]
    monitoring_guidance: list[str]
    seek_care_conditions: list[str]
    overall_evidence_level: str
    citations: list[dict[str, Any]]
    disclaimer: str
    emergency_message: str
    emergency_contact: dict[str, str] | None
    clarification_questions: list[str]
    needs_clarification: bool


@router.post("/chat", response_model=ChatResponse, summary="Send a message to MedicoBuddy")
async def chat(request: ChatRequest, req: Request) -> ChatResponse:
    """Process a user message through the MedicoBuddy workflow."""
    workflow = getattr(req.app.state, "workflow", None)
    if workflow is None:
        raise HTTPException(status_code=503, detail="Workflow not available")

    # Build user context
    try:
        age = AgeRange(request.age_range)
    except ValueError:
        age = AgeRange.UNKNOWN

    try:
        pregnancy = PregnancyStatus(request.pregnancy_status)
    except ValueError:
        pregnancy = PregnancyStatus.UNKNOWN

    user_context = UserContext(
        age_range=age,
        pregnancy_status=pregnancy,
        is_immunocompromised=request.is_immunocompromised,
        chronic_conditions=request.chronic_conditions,
        allergies=request.allergies,
        current_medications=request.current_medications,
        region=request.region,
    )

    # Build initial graph state
    from medicobuddy.models.symptom import SymptomReport

    initial_state: GraphState = {
        "user_message": request.message,
        "user_context": user_context,
        "symptom_report": SymptomReport(main_symptom=request.message),
        "conversation_history": [],
    }

    # Execute workflow
    try:
        result = await workflow.ainvoke(initial_state)
    except Exception:
        logger.error("Workflow execution failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Processing error")

    # Extract response
    final: MedicoBuddyResponse | None = result.get("final_response")
    if final is None:
        raise HTTPException(status_code=500, detail="No response generated")

    return ChatResponse(
        triage_outcome=final.triage_outcome.value,
        urgency_summary=final.urgency_summary,
        user_report_summary=final.user_report_summary,
        safe_comfort_steps=final.safe_comfort_steps,
        ayurveda_perspectives=[
            {
                "practice": ap.practice,
                "description": ap.description,
                "evidence_label": ap.evidence_label,
            }
            for ap in final.ayurveda_perspectives
        ],
        things_to_avoid=final.things_to_avoid,
        monitoring_guidance=final.monitoring_guidance,
        seek_care_conditions=final.seek_care_conditions,
        overall_evidence_level=final.overall_evidence_level.value,
        citations=[c.model_dump() for c in final.citations],
        disclaimer=final.disclaimer,
        emergency_message=final.emergency_message,
        emergency_contact=final.emergency_contact,
        clarification_questions=result.get("clarification_questions", []),
        needs_clarification=result.get("needs_clarification", False),
    )
