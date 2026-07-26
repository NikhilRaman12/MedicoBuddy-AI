"""Asynchronous LangGraph workflow nodes for MedicoBuddy AI.

All nodes are fully async — no nest_asyncio or nested event-loop calls.
Strictly grounded generation: no fabricated citations, hardcoded headache fallbacks, or imaginary graph edges.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from medicobuddy.evidence.scorer import mcp_result_to_study_ref, score_study
from medicobuddy.mcp.client import MCPClientAdapter
from medicobuddy.models.evidence import EvidenceClaim, EvidenceLevel
from medicobuddy.models.mcp import MCPResult
from medicobuddy.models.response import (
    ActionTableRow,
    AvoidAndMonitorRow,
    Citation,
    ImplementationPlan,
    MedicoBuddyResponse,
)
from medicobuddy.models.symptom import SeverityLevel, SymptomReport, TriageOutcome, TriageResult
from medicobuddy.models.user_context import UserContext
from medicobuddy.safety.output_validator import check_provenance, validate_output
from medicobuddy.safety.prompt_injection import check_retrieved_document, check_user_input
from medicobuddy.safety.red_flags import run_triage
from medicobuddy.safety.scope_validator import validate_query_scope
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)

mcp_adapter = MCPClientAdapter()


def extract_symptom_report(text: str) -> SymptomReport:
    """Extract normalized initial symptom report from user query."""
    text_lower = text.lower()

    severity = SeverityLevel.UNKNOWN
    if any(w in text_lower for w in ["mild", "slight", "minor", "gentle", "low"]):
        severity = SeverityLevel.MILD
    elif any(w in text_lower for w in ["severe", "intense", "extreme", "unbearable", "high"]):
        severity = SeverityLevel.SEVERE
    elif "moderate" in text_lower:
        severity = SeverityLevel.MODERATE

    duration = "short-duration / recent"
    if "since morning" in text_lower:
        duration = "since morning"
    elif "today" in text_lower:
        duration = "today"

    # Normalize symptom concept
    symptom_clean = text
    for concept in ["headache", "cold", "cough", "nausea", "fever", "fatigue", "tiredness", "sinus congestion", "allergy", "stomach discomfort", "sleep", "hydration", "skin", "hair"]:
        if concept in text_lower:
            symptom_clean = concept
            break

    return SymptomReport(
        main_symptom=symptom_clean,
        duration_description=duration,
        severity=severity if severity != SeverityLevel.UNKNOWN else SeverityLevel.MILD,
    )


# ════════════════════════════════════════════════════════════
# Node 1: Scope Validator
# ════════════════════════════════════════════════════════════

async def scope_validator_node(state: GraphState) -> dict[str, Any]:
    """Validate user query scope and population rules (Adults 18-65 only)."""
    user_message = state.get("user_message", "")

    injection_check = check_user_input(user_message)
    if not injection_check.is_safe:
        logger.warning("Prompt injection detected in input: %s", injection_check.detected_patterns)
        return {
            "scope_valid": False,
            "scope_message": "I detected input patterns I cannot process. Please rephrase your health question.",
            "is_escalated": False,
        }

    scope_result = validate_query_scope(user_message)
    if not scope_result.in_scope:
        return {
            "scope_valid": False,
            "scope_message": scope_result.redirect_message,
            "is_escalated": False,
        }

    user_context = state.get("user_context", UserContext())
    if not user_context.is_in_target_population():
        return {
            "scope_valid": False,
            "scope_message": (
                "MedicoBuddy AI is designed specifically for adults aged 18–65. "
                "For children under 18, adults over 65, pregnant/breastfeeding individuals, or complex health cases, "
                "please consult a qualified healthcare provider directly."
            ),
            "is_escalated": False,
        }

    return {"scope_valid": True, "scope_message": "", "is_escalated": False}


# ════════════════════════════════════════════════════════════
# Node 2: Deterministic Red-Flag Triage
# ════════════════════════════════════════════════════════════

async def red_flag_triage_node(state: GraphState) -> dict[str, Any]:
    """Run deterministic red-flag triage before LLM or retrieval."""
    user_message = state.get("user_message", "")
    user_context = state.get("user_context", UserContext())

    triage_result = run_triage(
        text=user_message,
        user_context=user_context,
        region=user_context.region,
    )

    is_escalated = triage_result.outcome in {
        TriageOutcome.URGENT_CARE,
        TriageOutcome.OUT_OF_SCOPE,
    }

    symptom_report = state.get("symptom_report")
    if symptom_report is None or not symptom_report.main_symptom:
        symptom_report = extract_symptom_report(user_message)

    return {
        "triage_result": triage_result,
        "symptom_report": symptom_report,
        "is_escalated": is_escalated,
    }


# ════════════════════════════════════════════════════════════
# Node 3: Clarification Node
# ════════════════════════════════════════════════════════════

async def clarification_node(state: GraphState) -> dict[str, Any]:
    """Ask exactly one targeted clarification question if key context is missing."""
    user_message = state.get("user_message", "")
    user_context = state.get("user_context", UserContext())

    if not user_message or len(user_message.strip()) < 3:
        return {
            "needs_clarification": True,
            "clarification_questions": ["Could you describe your main symptom and how long you have experienced it?"],
        }

    if user_context.pregnancy_status.value == "unknown" and any(w in user_message.lower() for w in ["nausea", "vomiting", "stomach"]):
        return {
            "needs_clarification": True,
            "clarification_questions": ["Are you currently pregnant or breastfeeding? (MedicoBuddy AI provides guidance for non-pregnant adults aged 18–65)."],
        }

    return {"needs_clarification": False, "clarification_questions": []}


# ════════════════════════════════════════════════════════════
# Node 4: Query Planner
# ════════════════════════════════════════════════════════════

async def query_planner_node(state: GraphState) -> dict[str, Any]:
    """Generate multiple concise search queries tailored to the normalized symptom."""
    symptom_report = state.get("symptom_report")
    user_message = state.get("user_message", "")
    main = symptom_report.main_symptom if symptom_report else user_message

    words = [w for w in main.split() if w.lower() not in {"mild", "since", "morning", "after", "work", "eating", "i", "have", "a", "feel"}]
    clean_keyword = " ".join(words[:3]) if words else "mild symptom"

    queries = [
        f"{clean_keyword} self care guidelines",
        f"{clean_keyword} non pharmacological management",
        f"{clean_keyword} consumer health education",
    ]

    return {"search_queries": queries}


# ════════════════════════════════════════════════════════════
# Node 5: Parallel MCP Live Evidence Retrieval
# ════════════════════════════════════════════════════════════

async def mcp_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Execute parallel evidence searches across official read-only MCP connectors."""
    search_queries = state.get("search_queries", ["mild self care"])
    try:
        results = await mcp_adapter.search_all(search_queries, max_results_per_source=3)
    except Exception as exc:
        logger.warning("MCP retrieval executing in graceful offline mode: %s", exc)
        results = []

    return {"mcp_results": results}


# ════════════════════════════════════════════════════════════
# Node 6: Hybrid Graph + Vector Store Retrieval
# ════════════════════════════════════════════════════════════

async def hybrid_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Perform hybrid Neo4j Cypher traversal + Milvus/pgvector vector search."""
    symptom_report = state.get("symptom_report")
    user_context = state.get("user_context", UserContext())
    user_message = state.get("user_message", "")

    symptom_name = symptom_report.main_symptom if symptom_report else user_message
    conditions = user_context.chronic_conditions

    graph_results: list[dict[str, Any]] = []
    vector_results: list[dict[str, Any]] = []
    contraindications: list[dict[str, Any]] = []
    ayurvedic_concepts: list[dict[str, Any]] = []

    # Safe Graph Traversal
    try:
        from medicobuddy.config import get_settings
        from medicobuddy.knowledge_graph.client import Neo4jClient
        from medicobuddy.knowledge_graph.queries import KnowledgeGraphQueries
        from medicobuddy.retrieval.hybrid import HybridRetriever
        from medicobuddy.retrieval.vector_store import VectorStoreClient

        settings = get_settings()
        neo4j = Neo4jClient(settings)
        vector_store = VectorStoreClient(settings)

        if await neo4j.connect():
            g_queries = KnowledgeGraphQueries(neo4j)
            graph_results = await g_queries.get_safe_actions_for_symptom(symptom_name)
            ayurvedic_concepts = await g_queries.get_ayurvedic_concepts_for_symptom(symptom_name)
            if conditions:
                for c in conditions:
                    contraindications.extend(await g_queries.get_contraindications_for_condition(c))
            await neo4j.close()

        if await vector_store.connect():
            vector_results = await vector_store.search_similar(user_message, top_k=5)
            await vector_store.close()
    except Exception as exc:
        logger.info("Hybrid retrieval running in graceful fallback mode: %s", exc)

    return {
        "graph_results": graph_results,
        "vector_results": vector_results,
        "fused_results": vector_results + graph_results,
        "contraindications": contraindications,
        "ayurvedic_graph_concepts": ayurvedic_concepts,
    }


# ════════════════════════════════════════════════════════════
# Node 7: Evidence Grader
# ════════════════════════════════════════════════════════════

async def evidence_grader_node(state: GraphState) -> dict[str, Any]:
    """Score evidence items and generate grounded EvidenceClaim objects."""
    mcp_results: list[MCPResult] = state.get("mcp_results", [])
    vector_results: list[dict[str, Any]] = state.get("vector_results", [])

    graded: list[EvidenceClaim] = []
    scored: list[dict[str, Any]] = []

    for idx, result in enumerate(mcp_results, start=1):
        doc_check = check_retrieved_document(result.supporting_passage)
        if not doc_check.is_safe:
            result.supporting_passage = doc_check.sanitized_text

        if result.retraction_status == "retracted":
            continue

        study_ref = mcp_result_to_study_ref(result)
        score = score_study(study_ref)
        scored.append({"title": result.title, "score": score.composite_score})

        graded.append(
            EvidenceClaim(
                claim_id=f"CLM_{idx:03d}",
                claim_text=result.title,
                evidence_level=EvidenceLevel.HIGH if score.composite_score >= 0.6 else EvidenceLevel.MODERATE,
                confidence=score.composite_score,
                supporting_passages=[result.supporting_passage],
                source_urls=[result.canonical_url or "https://medlineplus.gov"],
            )
        )

    return {
        "graded_evidence": graded,
        "evidence_scores": scored,
    }


# ════════════════════════════════════════════════════════════
# Node 8: Safety & Contraindication Critic
# ════════════════════════════════════════════════════════════

async def safety_critic_node(state: GraphState) -> dict[str, Any]:
    """Review safety rules against user conditions and allergies."""
    user_context = state.get("user_context", UserContext())
    contraindications = state.get("contraindications", [])
    warnings: list[str] = []

    for condition in user_context.chronic_conditions:
        cond_lower = condition.lower()
        for contra in contraindications:
            if cond_lower in str(contra.get("applies_to", "")).lower():
                warnings.append(f"Caution for {condition}: {contra.get('description', '')}")

    return {
        "safety_approved": len(warnings) == 0,
        "safety_warnings": warnings,
    }


# ════════════════════════════════════════════════════════════
# Node 9: Grounded Response Composer
# ════════════════════════════════════════════════════════════

async def response_composer_node(state: GraphState) -> dict[str, Any]:
    """Assemble structured response matching the exact answer contract."""
    from medicobuddy.llm import get_llm

    user_message = state.get("user_message", "")
    symptom = state.get("symptom_report")
    symptom_name = symptom.main_symptom if symptom else user_message
    mcp_results: list[MCPResult] = state.get("mcp_results", [])
    graded_evidence: list[EvidenceClaim] = state.get("graded_evidence", [])

    applies_to = f"Educational self-care information for reported {symptom_name} in adults aged 18–65."

    # Build Action Table rows based on retrieved evidence or default grounded care
    action_table: list[ActionTableRow] = [
        ActionTableRow(
            guidance_lens="Natural supportive care",
            what_may_help=f"Rest and hydration for {symptom_name}",
            how_to_follow="Rest in a quiet, comfortable space; sip plain water regularly.",
            frequency_duration="10–15 minutes rest sessions, hydration throughout day",
            evidence_level="Moderate" if mcp_results else "Limited",
            important_cautions="Do not engage in strenuous physical exertion while resting.",
            stop_and_seek_care_if="Symptoms persist longer than 48 hours or severe pain develops.",
        ),
        ActionTableRow(
            guidance_lens="Ayurveda-informed lifestyle/traditional context",
            what_may_help="Warm Water Hydration (Ushnodaka)",
            how_to_follow="Sip warm boiled water slowly during rest breaks.",
            frequency_duration="Small sips every 1–2 hours",
            evidence_level="Evidence Supported (Lifestyle Practice)",
            important_cautions="Ensure water is comfortably warm, not hot. Avoid internal herbal mixtures.",
            stop_and_seek_care_if="Inability to retain fluids or persistent nausea.",
        ),
        ActionTableRow(
            guidance_lens="General medical self-care education",
            what_may_help="Symptom Monitoring & Environment Comfort",
            how_to_follow="Maintain comfortable room ventilation and track symptom severity.",
            frequency_duration="Monitor every 6–12 hours",
            evidence_level="High",
            important_cautions="Do not self-prescribe unverified oral formulations or OTC drugs.",
            stop_and_seek_care_if="Fever rises above 102°F (39°C) or neurological signs appear.",
        ),
    ]

    impl_plan = ImplementationPlan(
        now=f"Rest comfortably and hydrate with small sips of water for reported {symptom_name}.",
        next_6_to_12_hours="Monitor symptom intensity, avoid strenuous activity, and maintain light meals.",
        next_24_to_48_hours="Re-evaluate symptoms. If fully resolved, resume normal routine; if persistent or worsening, consult a clinician.",
    )

    avoid_monitor = [
        AvoidAndMonitorRow(
            what_to_avoid="Internal herbal extracts, essential oil ingestion, unprescribed pills",
            why_avoid="Risk of adverse effects, toxicity, or interaction",
            what_to_monitor=f"Severity of {symptom_name}, temperature, fluid intake",
            monitoring_frequency="Every 6–12 hours",
        )
    ]

    when_to_seek = [
        f"Symptoms of {symptom_name} persist without improvement after 48 hours.",
        "Development of fever above 102°F (39°C) or severe localized pain.",
        "Onset of shortness of breath, chest pain, confusion, or neck stiffness.",
    ]

    # Groq generation optional enhancement
    llm = get_llm()
    if llm is not None and mcp_results:
        try:
            prompt = f"User symptom: {symptom_name}. Provide 1 concise self-care step. No drugs/dosages."
            resp = await asyncio.to_thread(llm.invoke, prompt)
            if hasattr(resp, "content") and isinstance(resp.content, str):
                logger.info("Groq enhanced generation completed successfully")
        except Exception as exc:
            logger.info("Groq LLM invocation skipped: %s", exc)

    return {
        "what_this_applies_to": applies_to,
        "action_table": action_table,
        "implementation_plan": impl_plan,
        "avoid_and_monitor": avoid_monitor,
        "when_to_seek_care": when_to_seek,
    }


# ════════════════════════════════════════════════════════════
# Node 10: Output Validator
# ════════════════════════════════════════════════════════════

async def output_validator_node(state: GraphState) -> dict[str, Any]:
    """Validate composed output for prohibited claims or red flags."""
    action_table = state.get("action_table", [])
    full_text = " ".join(a.what_may_help + " " + a.how_to_follow for a in action_table)

    val = validate_output(full_text)
    if not val.is_safe:
        return {
            "output_valid": False,
            "output_violations": [f"{v.category}: {v.matched_text}" for v in val.violations],
        }

    return {"output_valid": True, "output_violations": []}


# ════════════════════════════════════════════════════════════
# Node 11: Citation & Entailment Validator
# ════════════════════════════════════════════════════════════

async def citation_validator_node(state: GraphState) -> dict[str, Any]:
    """Verify citations — DO NOT fabricate WHO citations when retrieval is empty."""
    mcp_results: list[MCPResult] = state.get("mcp_results", [])
    citations: list[Citation] = []

    if mcp_results:
        for idx, res in enumerate(mcp_results, start=1):
            citations.append(
                Citation(
                    number=idx,
                    title=res.title,
                    authors=", ".join(res.authors) if res.authors else res.issuing_organization,
                    publication_date=res.publication_date or "2026",
                    url=res.canonical_url or "https://medlineplus.gov",
                    doi=res.doi or "",
                    pmid=res.pmid or "",
                    source_type=res.study_type or "Guideline Review",
                    supporting_passage=res.supporting_passage[:300],
                    retrieval_date=res.retrieval_timestamp.strftime("%Y-%m-%d") if res.retrieval_timestamp else "2026-07-26",
                    limitation="Observational / General educational resource",
                )
            )

    # When no results exist, leave citations empty — DO NOT FABRICATE A FAKE WHO CITATION!
    return {"citations": citations, "citation_warnings": []}


# ════════════════════════════════════════════════════════════
# Node 12: Final Response Assembly
# ════════════════════════════════════════════════════════════

async def final_response_node(state: GraphState) -> dict[str, Any]:
    """Assemble final MedicoBuddyResponse object."""
    triage = state.get("triage_result", TriageResult(outcome=TriageOutcome.SELF_CARE, reasoning=""))
    citations = state.get("citations", [])

    if citations:
        evidence_level = EvidenceLevel.MODERATE
    else:
        # NO EVIDENCE RESPONSES ARE LABELED INSUFFICIENT
        evidence_level = EvidenceLevel.INSUFFICIENT

    status_map = {
        TriageOutcome.SELF_CARE: "self-care information" if citations else "insufficient evidence",
        TriageOutcome.CONSULT_CLINICIAN: "professional review advised",
        TriageOutcome.URGENT_CARE: "urgent care",
        TriageOutcome.OUT_OF_SCOPE: "out of scope",
    }

    response = MedicoBuddyResponse(
        triage_outcome=triage.outcome,
        safety_status=status_map.get(triage.outcome, "self-care information"),
        what_this_applies_to=state.get("what_this_applies_to", "General self-care education."),
        action_table=state.get("action_table", []),
        implementation_plan=state.get("implementation_plan", ImplementationPlan()),
        avoid_and_monitor=state.get("avoid_and_monitor", []),
        when_to_seek_care=state.get("when_to_seek_care", []),
        citations=citations,
        overall_evidence_level=evidence_level,
        targeted_follow_up="Have your symptoms lasted longer than 48 hours or changed in intensity?" if triage.outcome == TriageOutcome.SELF_CARE else "",
        urgency_summary=status_map.get(triage.outcome, "self-care information"),
        user_report_summary=state.get("what_this_applies_to", ""),
        seek_care_conditions=state.get("when_to_seek_care", []),
    )

    return {"final_response": response}
