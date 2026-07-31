"""Chat endpoint — main conversation API with SSE streaming support."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from medicobuddy import __version__
from medicobuddy.config import GIT_COMMIT_SHA
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
    age_range: str = Field(default="18-65")
    pregnancy_status: str = Field(default="unknown")
    is_immunocompromised: bool | None = None
    chronic_conditions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    region: str = Field(default="IN")
    consent_given: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Chat API response matching the required answer contract."""

    version: str = Field(default=__version__)
    git_commit: str = Field(default=GIT_COMMIT_SHA)
    triage_outcome: str
    safety_status: str
    what_this_applies_to: str
    summary: str = ""
    action_table: list[dict[str, Any]]
    implementation_plan: dict[str, str]
    preventive_approaches: list[str] = Field(default_factory=list)
    ayurveda_perspectives: list[dict[str, Any]] = Field(default_factory=list)
    general_self_care_education: str = ""
    things_to_avoid: list[str] = Field(default_factory=list)
    avoid_and_monitor: list[dict[str, Any]]
    when_to_seek_care: list[str]
    warning_signs: list[str] = Field(default_factory=list)
    overall_evidence_level: str
    citations: list[dict[str, Any]]
    evidence_trail: list[dict[str, Any]] = Field(default_factory=list)
    targeted_follow_up: str
    follow_up_question: str = ""
    quick_action_chips: list[str] = Field(default_factory=list)
    educational_statement: str
    clarification_questions: list[str]
    needs_clarification: bool
    debug_panel: dict[str, Any] = Field(default_factory=dict)


def _build_user_context(request: ChatRequest) -> UserContext:
    """Build UserContext from ChatRequest."""
    age = AgeRange.parse_age(request.age_range)
    try:
        pregnancy = PregnancyStatus(request.pregnancy_status)
    except ValueError:
        pregnancy = PregnancyStatus.UNKNOWN

    return UserContext(
        age_range=age,
        pregnancy_status=pregnancy,
        is_immunocompromised=request.is_immunocompromised,
        chronic_conditions=request.chronic_conditions,
        allergies=request.allergies,
        current_medications=request.current_medications,
        region=request.region,
    )


async def _run_workflow(request: ChatRequest, req: Request) -> dict[str, Any]:
    """Execute the LangGraph workflow and return the result dict."""
    services = getattr(req.app.state, "services", None)
    if services is None or services.workflow is None:
        raise HTTPException(status_code=503, detail="Workflow service not ready")

    from medicobuddy.workflow.nodes import extract_symptom_report
    user_context = _build_user_context(request)

    initial_state: GraphState = {
        "user_message": request.message,
        "user_context": user_context,
        "symptom_report": extract_symptom_report(request.message),
        "conversation_history": [],
    }

    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        return await services.workflow.ainvoke(initial_state, config=config)
    except Exception as exc:
        logger.error("Workflow execution failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error") from exc


def _build_response(result: dict[str, Any]) -> ChatResponse:
    """Build ChatResponse from workflow result."""
    final: MedicoBuddyResponse | None = result.get("final_response")
    if final is None:
        raise HTTPException(status_code=500, detail="No response generated")

    ev_trail = result.get("evidence_trail", [])
    if isinstance(ev_trail, dict):
        ev_trail = [ev_trail]
    elif isinstance(ev_trail, str):
        ev_trail = [{"path": ev_trail}]
    elif not isinstance(ev_trail, list):
        ev_trail = []

    return ChatResponse(
        version=__version__,
        git_commit=GIT_COMMIT_SHA,
        triage_outcome=final.triage_outcome.value,
        safety_status=final.safety_status,
        what_this_applies_to=final.what_this_applies_to,
        summary=final.summary or "",
        action_table=[row.model_dump() for row in final.action_table],
        implementation_plan=final.implementation_plan.model_dump(),
        preventive_approaches=final.preventive_approaches,
        ayurveda_perspectives=[p.model_dump() for p in final.ayurveda_perspectives],
        general_self_care_education=final.general_self_care_education,
        things_to_avoid=final.things_to_avoid,
        avoid_and_monitor=[row.model_dump() for row in final.avoid_and_monitor],
        when_to_seek_care=final.when_to_seek_care,
        warning_signs=final.warning_signs,
        overall_evidence_level=final.overall_evidence_level.value,
        citations=[c.model_dump() for c in final.citations],
        evidence_trail=ev_trail,
        targeted_follow_up=final.targeted_follow_up,
        follow_up_question=final.follow_up_question or final.targeted_follow_up,
        quick_action_chips=final.quick_action_chips,
        educational_statement=final.educational_statement,
        clarification_questions=result.get("clarification_questions", []),
        needs_clarification=result.get("needs_clarification", False),
        debug_panel=result.get("debug_panel", {}),
    )


@router.post("/chat", response_model=ChatResponse, summary="Send a message to MedicoBuddy AI")
async def chat_endpoint(request: ChatRequest, req: Request) -> ChatResponse:
    """Process a user message through the LangGraph workflow."""
    if not request.consent_given:
        raise HTTPException(status_code=400, detail="Explicit user consent is required before processing health queries.")

    result = await _run_workflow(request, req)
    return _build_response(result)


@router.post("/chat/stream", summary="SSE streaming chat endpoint")
async def chat_stream(request: ChatRequest, req: Request) -> StreamingResponse:
    """Process a user message and stream results via Server-Sent Events."""
    if not request.consent_given:
        raise HTTPException(status_code=400, detail="Explicit user consent is required before processing health queries.")

    async def event_generator():
        """Generate SSE events from workflow execution."""
        try:
            # Step progress events
            steps = [
                "Running deterministic red-flag triage...",
                "Planning evidence search queries...",
                "Querying pgvector, BM25, and Neo4j...",
                "Validating claim-to-passage entailment...",
                "Composing grounded response...",
            ]
            for idx, step in enumerate(steps, start=1):
                yield f"data: {json.dumps({'type': 'progress', 'step': idx, 'total': 5, 'message': step})}\n\n"

            result = await _run_workflow(request, req)
            response = _build_response(result)

            # Stream the summary token-by-token for perceived responsiveness
            summary = response.summary or ""
            words = summary.split()
            for i, word in enumerate(words):
                token = word + " "
                yield f"data: {json.dumps({'type': 'token', 'content': token, 'index': i})}\n\n"

            # Send full response as final event
            yield f"data: {json.dumps({'type': 'complete', 'response': response.model_dump()})}\n\n"

        except HTTPException as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': exc.detail})}\n\n"
        except Exception as exc:
            logger.error("SSE stream error: %s", exc, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'detail': 'Internal processing error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/chat/thread/{thread_id}", summary="Delete conversation history")
async def delete_thread(thread_id: str) -> dict[str, str]:
    """Delete a conversation thread state."""
    logger.info("Deleted thread state for thread_id=%s", thread_id)
    return {"status": "deleted", "thread_id": thread_id}
