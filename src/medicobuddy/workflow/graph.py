"""LangGraph workflow definition — the complete MedicoBuddy processing pipeline."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from medicobuddy.workflow.nodes import (
    citation_validator_node,
    clarification_node,
    evidence_grader_node,
    final_response_node,
    hybrid_retrieval_node,
    language_router_node,
    mcp_retrieval_node,
    output_validator_node,
    query_planner_node,
    red_flag_triage_node,
    response_composer_node,
    safety_critic_node,
    scope_validator_node,
    structured_translation_node,
)
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)


def _should_escalate(state: GraphState) -> str:
    """Route to escalation or continue normal flow."""
    if state.get("is_escalated"):
        return "escalate"
    return "continue"


def _scope_check(state: GraphState) -> str:
    """Route based on scope validation result."""
    if not state.get("scope_valid", True):
        return "out_of_scope"
    return "in_scope"


def _needs_clarification(state: GraphState) -> str:
    """Route based on whether clarification is needed."""
    symptom = state.get("symptom_report")
    has_symptom = bool(symptom and symptom.main_symptom and len(symptom.main_symptom.strip()) >= 3)
    if state.get("needs_clarification") and not has_symptom:
        return "clarify"
    return "proceed"


def _output_check(state: GraphState) -> str:
    """Route based on output validation result."""
    if not state.get("output_valid", True):
        return "recompose"
    return "valid"


def build_workflow() -> StateGraph:
    """Build the complete MedicoBuddy LangGraph workflow.

    Flow:
        User Input → Language Router → Scope Validator → Red-Flag Triage → Clarification
        → Query Planner → MCP Retrieval → Hybrid Retrieval
        → Evidence Grader → Safety Critic → Response Composer
        → Output Validator → Citation Validator → Structured Translation → Final Response
    """
    workflow = StateGraph(GraphState)

    # ── Add all nodes ────────────────────────────────────────
    workflow.add_node("language_router", language_router_node)
    workflow.add_node("scope_validator", scope_validator_node)
    workflow.add_node("red_flag_triage", red_flag_triage_node)
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("query_planner", query_planner_node)
    workflow.add_node("mcp_retrieval", mcp_retrieval_node)
    workflow.add_node("hybrid_retrieval", hybrid_retrieval_node)
    workflow.add_node("evidence_grader", evidence_grader_node)
    workflow.add_node("safety_critic", safety_critic_node)
    workflow.add_node("response_composer", response_composer_node)
    workflow.add_node("output_validator", output_validator_node)
    workflow.add_node("citation_validator", citation_validator_node)
    workflow.add_node("structured_translation", structured_translation_node)
    workflow.add_node("final_response", final_response_node)

    # ── Entry point ──────────────────────────────────────────
    workflow.set_entry_point("language_router")
    workflow.add_edge("language_router", "scope_validator")

    # ── Edges with routing ───────────────────────────────────

    # Scope validator → either out_of_scope (→ final) or in_scope (→ triage)
    workflow.add_conditional_edges(
        "scope_validator",
        _scope_check,
        {
            "out_of_scope": "structured_translation",
            "in_scope": "red_flag_triage",
        },
    )

    # Red flag triage → either escalate (→ final) or continue (→ clarification)
    workflow.add_conditional_edges(
        "red_flag_triage",
        _should_escalate,
        {
            "escalate": "response_composer",
            "continue": "clarification",
        },
    )

    # Clarification → either clarify (→ final w/ questions) or proceed (→ query planner)
    workflow.add_conditional_edges(
        "clarification",
        _needs_clarification,
        {
            "clarify": "structured_translation",
            "proceed": "query_planner",
        },
    )

    # Linear flow: query planner → MCP → hybrid → evidence → safety → compose
    workflow.add_edge("query_planner", "mcp_retrieval")
    workflow.add_edge("mcp_retrieval", "hybrid_retrieval")
    workflow.add_edge("hybrid_retrieval", "evidence_grader")
    workflow.add_edge("evidence_grader", "safety_critic")
    workflow.add_edge("safety_critic", "response_composer")

    # Response composer → output validator
    workflow.add_edge("response_composer", "output_validator")

    # Output validator → either recompose or continue to citation validator
    workflow.add_conditional_edges(
        "output_validator",
        _output_check,
        {
            "recompose": "response_composer",
            "valid": "citation_validator",
        },
    )

    # Citation validator → structured translation → final response → END
    workflow.add_edge("citation_validator", "structured_translation")
    workflow.add_edge("structured_translation", "final_response")
    workflow.add_edge("final_response", END)

    return workflow


from langgraph.checkpoint.memory import MemorySaver


def create_app() -> Any:
    """Create and compile the LangGraph application with MemorySaver checkpointer."""
    workflow = build_workflow()
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)
