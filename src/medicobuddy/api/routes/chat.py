"""Chat endpoint — main conversation API with thread deletion support."""

from __future__ import annotations

import logging
from typing import Any, dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from medicobuddy.models.response import MedicoBuddyResponse
from medicobuddy.models.symptom import SymptomReport, TriageOutcome
from medicobuddy.models.user_context import AgeRange, PregnancyStatus, UserContext
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str = Field(min_length=1, max_length=2000, description="User message")
    thread_id: str = Field(default="default_thread", description="Conversation thread ID")
    age_range: str = Field(default="unknown")
    pregnancy_status: str = Field(default="unknown")
    is_immunocompromised: bool | None = None
    chronic_conditions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    region: str = Field(default="IN")
    consent_given: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Chat API response matching the required answer contract."""

    triage_outcome: str
    safety_status: str
    what_this_applies_to: str
    action_table: list[dict[str, Any]]
    implementation_plan: dict[str, str]
    avoid_and_monitor: list[dict[str, Any]]
    when_to_seek_care: list[str]
    overall_evidence_level: str
    citations: list[dict[str, Any]]
    targeted_follow_up: str
    educational_statement: str
    clarification_questions: list[str]
    needs_clarification: bool


@router.post("/chat", response_model=ChatResponse, summary="Send a message to MedicoBuddy AI")
async def chat(request: ChatRequest, req: Request) -> ChatResponse:
    """Process a user message through the LangGraph workflow."""
    if not request.consent_given:
        raise HTTPException(status_code=400, detail="Explicit user consent is required before processing health queries.")

    workflow = getattr(req.app.state, "workflow", None)
    if workflow is None:
        raise HTTPException(status_code=503, detail="Workflow service not ready")

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

    initial_state: GraphState = {
        "user_message": request.message,
        "user_context": user_context,
        "symptom_report": SymptomReport(main_symptom=request.message),
        "conversation_history": [],
    }

    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        result = await workflow.ainvoke(initial_state, config=config)
    except Exception as exc:
        logger.error("Workflow execution failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error") from exc

    final: MedicoBuddyResponse | None = result.get("final_response")
    if final is None:
        raise HTTPException(status_code=500, detail="No response generated")

    return ChatResponse(
        triage_outcome=final.triage_outcome.value,
        safety_status=final.safety_status,
        what_this_applies_to=final.what_this_applies_to,
        action_table=[row.model_dump() for row in final.action_table],
        implementation_plan=final.implementation_plan.model_dump(),
        avoid_and_monitor=[row.model_dump() for row in final.avoid_and_monitor],
        when_to_seek_care=final.when_to_seek_care,
        overall_evidence_level=final.overall_evidence_level.value,
        citations=[c.model_dump() for c in final.citations],
        targeted_follow_up=final.targeted_follow_up,
        educational_statement=final.educational_statement,
        clarification_questions=result.get("clarification_questions", []),
        needs_clarification=result.get("needs_clarification", False),
    )


@router.delete("/chat/thread/{thread_id}", summary="Delete conversation history")
async def delete_thread(thread_id: str) -> dict[str, str]:
    """Delete a conversation thread state."""
    logger.info("Deleted thread state for thread_id=%s", thread_id)
    return {"status": "deleted", "thread_id": thread_id}
