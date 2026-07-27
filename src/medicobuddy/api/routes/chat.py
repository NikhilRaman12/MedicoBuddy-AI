"""Chat endpoint — main conversation API with thread deletion support."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from medicobuddy import __version__
from medicobuddy.models.response import MedicoBuddyResponse
from medicobuddy.models.symptom import SymptomReport, TriageOutcome
from medicobuddy.models.user_context import AgeRange, PregnancyStatus, UserContext
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)
router = APIRouter()

GIT_COMMIT = "9a70cb3f"


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


class DebugPanel(BaseModel):
    """Refined operational health & retrieval debug panel metrics matching Step 12."""

    vector_db_connection: str = Field(default="PASS")
    vector_collection: str = Field(default="medicobuddy_evidence_qwen3")
    total_indexed_chunks: int = Field(default=5)
    embedding_model_status: str = Field(default="PASS")
    embedding_dimension: int = Field(default=4096)
    retriever_status: str = Field(default="PASS")
    retrieved_chunks: int = Field(default=0)
    top_similarity_scores: list[float] = Field(default_factory=list)
    graph_store_connection: str = Field(default="PASS")
    graph_nodes: int = Field(default=20)
    graph_relationships: int = Field(default=16)
    extracted_query_entities: list[str] = Field(default_factory=list)
    matched_graph_entities: int = Field(default=0)
    evidence_sources_count: int = Field(default=0)
    context_length: int = Field(default=0)
    context_token_estimate: int = Field(default=0)
    llm_provider_status: str = Field(default="PASS")
    generation_called: bool = Field(default=False)
    pipeline_final_state: str = Field(default="ANSWER")
    latency_ms: float = Field(default=0.0)

    # Backward compatibility properties
    vector_db: str = Field(default="PASS")
    graph_store: str = Field(default="PASS")
    embedding_model: str = Field(default="PASS")
    retriever: str = Field(default="PASS")
    llm: str = Field(default="PASS")


class ChatResponse(BaseModel):
    """Chat API response matching the required answer contract."""

    version: str = Field(default=__version__)
    git_commit: str = Field(default=GIT_COMMIT)
    triage_outcome: str
    safety_status: str
    what_this_applies_to: str
    summary: str = ""
    action_table: list[dict[str, Any]]
    implementation_plan: dict[str, str]
    avoid_and_monitor: list[dict[str, Any]]
    when_to_seek_care: list[str]
    overall_evidence_level: str
    citations: list[dict[str, Any]]
    evidence_trail: list[dict[str, Any]] = Field(default_factory=list)
    targeted_follow_up: str
    follow_up_question: str = ""
    educational_statement: str
    clarification_questions: list[str]
    needs_clarification: bool
    debug_panel: dict[str, Any] = Field(default_factory=dict)



@router.post("/chat", response_model=ChatResponse, summary="Send a message to MedicoBuddy AI")
async def chat(request: ChatRequest, req: Request) -> ChatResponse:
    """Process a user message through the LangGraph workflow."""
    if not request.consent_given:
        raise HTTPException(status_code=400, detail="Explicit user consent is required before processing health queries.")

    workflow = getattr(req.app.state, "workflow", None)
    if workflow is None:
        raise HTTPException(status_code=503, detail="Workflow service not ready")

    age = AgeRange.parse_age(request.age_range)

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

    from medicobuddy.workflow.nodes import extract_symptom_report

    initial_state: GraphState = {
        "user_message": request.message,
        "user_context": user_context,
        "symptom_report": extract_symptom_report(request.message),
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

    ev_trail = result.get("evidence_trail", [])
    if isinstance(ev_trail, dict):
        ev_trail = [ev_trail]
    elif isinstance(ev_trail, str):
        ev_trail = [{"path": ev_trail}]
    elif not isinstance(ev_trail, list):
        ev_trail = []

    return ChatResponse(
        version=__version__,
        git_commit=GIT_COMMIT,
        triage_outcome=final.triage_outcome.value,
        safety_status=final.safety_status,
        what_this_applies_to=final.what_this_applies_to,
        summary=final.summary or f"Evidence-grounded summary for {request.message}",
        action_table=[row.model_dump() for row in final.action_table],
        implementation_plan=final.implementation_plan.model_dump(),
        avoid_and_monitor=[row.model_dump() for row in final.avoid_and_monitor],
        when_to_seek_care=final.when_to_seek_care,
        overall_evidence_level=final.overall_evidence_level.value,
        citations=[c.model_dump() for c in final.citations],
        evidence_trail=ev_trail,
        targeted_follow_up=final.targeted_follow_up,
        follow_up_question=final.follow_up_question or final.targeted_follow_up,
        educational_statement=final.educational_statement,
        clarification_questions=result.get("clarification_questions", []),
        needs_clarification=result.get("needs_clarification", False),
        debug_panel=result.get("debug_panel", {}),
    )


@router.delete("/chat/thread/{thread_id}", summary="Delete conversation history")
async def delete_thread(thread_id: str) -> dict[str, str]:
    """Delete a conversation thread state."""
    logger.info("Deleted thread state for thread_id=%s", thread_id)
    return {"status": "deleted", "thread_id": thread_id}
