"""LangGraph state definition for the MedicoBuddy workflow."""

from __future__ import annotations

from typing import Any, TypedDict

from medicobuddy.models.evidence import EvidenceClaim
from medicobuddy.models.mcp import MCPResult
from medicobuddy.models.response import (
    ActionTableRow,
    AvoidAndMonitorRow,
    AyurvedaPerspective,
    Citation,
    ImplementationPlan,
    MedicoBuddyResponse,
)
from medicobuddy.models.symptom import SymptomReport, TriageResult
from medicobuddy.models.user_context import UserContext


class GraphState(TypedDict, total=False):
    """State passed through the LangGraph workflow.

    Each node reads from and writes to specific keys in this state dict.
    """

    # ── Request Isolation & Anti-Caching ───────────────────────
    request_id: str
    query_hash: str
    retrieval_query_hash: str

    # ── Input & Context ──────────────────────────────────────
    user_message: str
    original_query: str
    normalized_query: dict[str, Any]
    raw_query: str
    conversation_history: list[dict[str, str]]
    conversation_context: str
    user_context: UserContext
    detected_language: str
    language: str
    entities: list[str]
    symptom_entities: list[str]

    # ── Entity Extraction ────────────────────────────────────
    extracted_entities: dict[str, list[str]]  # symptom, remedy, population, evidence, safety
    entity_synonyms: dict[str, list[str]]     # entity -> expanded synonyms

    # ── Scope & Triage ───────────────────────────────────────
    symptom_report: SymptomReport
    scope_valid: bool
    scope_message: str
    triage_result: TriageResult
    is_escalated: bool

    # ── Clarification ────────────────────────────────────────
    needs_clarification: bool
    clarification_questions: list[str]

    # ── Query Planning & Retrieval ───────────────────────────
    search_queries: list[str]
    mcp_results: list[MCPResult]
    graph_results: list[dict[str, Any]]
    vector_results: list[dict[str, Any]]
    bm25_results: list[dict[str, Any]]
    vector_docs: list[dict[str, Any]]
    vector_scores: list[float]
    graph_entities: list[dict[str, Any]]
    graph_paths: list[dict[str, Any]]
    graph_context: list[dict[str, Any]]
    merged_evidence: str
    reranked_evidence: list[dict[str, Any]]
    grounded_context: str
    merged_context: str
    context: str
    context_tokens: int
    evidence_count: int
    evidence_status: str
    evidence_sufficient: bool
    fused_results: list[dict[str, Any]]
    contraindications: list[dict[str, Any]]
    ayurvedic_graph_concepts: list[dict[str, Any]]
    retrieval_status: dict[str, Any]
    retrieval_diagnostics: dict[str, Any]
    dependency_errors: list[str]
    errors: list[str]

    # ── Evidence Grading ─────────────────────────────────────
    graded_evidence: list[EvidenceClaim]
    evidence_scores: list[dict[str, Any]]

    # ── Safety Review ────────────────────────────────────────
    safety_approved: bool
    safety_warnings: list[str]
    safety_status: str

    # ── Response Composition & Output Contract ───────────────
    draft_response: str
    final_answer: str
    what_this_applies_to: str
    summary: str
    action_table: list[ActionTableRow]
    implementation_plan: ImplementationPlan
    avoid_and_monitor: list[AvoidAndMonitorRow]
    when_to_seek_care: list[str]
    follow_up_question: str
    safe_comfort_steps: list[str]
    ayurveda_perspectives: list[AyurvedaPerspective]
    things_to_avoid: list[str]
    preventive_approaches: list[str]
    general_self_care_education: str
    warning_signs: list[str]
    quick_action_chips: list[str]
    monitoring_guidance: list[str]
    seek_care_conditions: list[str]
    generation_called: bool

    # ── Output & Citation Validation ─────────────────────────
    output_valid: bool
    output_violations: list[str]
    citations: list[Citation]
    citation_warnings: list[str]
    evidence_trail: list[dict[str, Any]]

    # ── Final Response ───────────────────────────────────────
    final_response: MedicoBuddyResponse
    debug_panel: dict[str, Any]
    error: str
