"""LangGraph state definition for the MedicoBuddy workflow."""

from __future__ import annotations

from typing import Any, TypedDict

from medicobuddy.models.evidence import EvidenceClaim
from medicobuddy.models.mcp import MCPResult
from medicobuddy.models.response import AyurvedaPerspective, Citation, MedicoBuddyResponse
from medicobuddy.models.symptom import SymptomReport, TriageResult
from medicobuddy.models.user_context import UserContext


class GraphState(TypedDict, total=False):
    """State passed through the LangGraph workflow.

    Each node reads from and writes to specific keys in this state dict.
    """

    # ── Input ────────────────────────────────────────────────
    user_message: str
    conversation_history: list[dict[str, str]]

    # ── Scope & Triage ───────────────────────────────────────
    user_context: UserContext
    symptom_report: SymptomReport
    scope_valid: bool
    scope_message: str
    triage_result: TriageResult
    is_escalated: bool

    # ── Clarification ────────────────────────────────────────
    needs_clarification: bool
    clarification_questions: list[str]

    # ── Query Planning ───────────────────────────────────────
    search_queries: list[str]

    # ── MCP Retrieval ────────────────────────────────────────
    mcp_results: list[MCPResult]

    # ── Hybrid Retrieval ─────────────────────────────────────
    graph_results: list[dict[str, Any]]
    vector_results: list[dict[str, Any]]
    fused_results: list[dict[str, Any]]
    contraindications: list[dict[str, Any]]
    ayurvedic_graph_concepts: list[dict[str, Any]]

    # ── Evidence Grading ─────────────────────────────────────
    graded_evidence: list[EvidenceClaim]
    evidence_scores: list[dict[str, Any]]

    # ── Safety Review ────────────────────────────────────────
    safety_approved: bool
    safety_warnings: list[str]

    # ── Response Composition ─────────────────────────────────
    draft_response: str
    safe_comfort_steps: list[str]
    ayurveda_perspectives: list[AyurvedaPerspective]
    things_to_avoid: list[str]
    monitoring_guidance: list[str]
    seek_care_conditions: list[str]

    # ── Output Validation ────────────────────────────────────
    output_valid: bool
    output_violations: list[str]

    # ── Citation Validation ──────────────────────────────────
    citations: list[Citation]
    citation_warnings: list[str]

    # ── Final Response ───────────────────────────────────────
    final_response: MedicoBuddyResponse
    error: str
