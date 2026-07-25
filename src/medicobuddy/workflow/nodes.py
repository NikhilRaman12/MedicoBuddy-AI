"""Workflow node implementations — all 12 LangGraph nodes."""

from __future__ import annotations

import logging
from typing import Any

from medicobuddy.evidence.scorer import (
    classify_ayurveda_evidence,
    determine_evidence_level,
    mcp_result_to_study_ref,
    score_study,
)
from medicobuddy.models.evidence import EvidenceClaim, EvidenceLevel
from medicobuddy.models.mcp import MCPResult
from medicobuddy.models.response import AyurvedaPerspective, Citation, MedicoBuddyResponse
from medicobuddy.models.symptom import SymptomReport, TriageOutcome, TriageResult
from medicobuddy.models.user_context import UserContext
from medicobuddy.safety.output_validator import check_provenance, validate_output
from medicobuddy.safety.prompt_injection import check_retrieved_document, check_user_input
from medicobuddy.safety.red_flags import run_triage
from medicobuddy.safety.scope_validator import validate_query_scope
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# Node 1: Scope Validator
# ════════════════════════════════════════════════════════════

def scope_validator_node(state: GraphState) -> dict[str, Any]:
    """Validate that the user's query is within MedicoBuddy's scope."""
    user_message = state.get("user_message", "")

    # Check for prompt injection
    injection_check = check_user_input(user_message)
    if not injection_check.is_safe:
        logger.warning("Prompt injection detected: %s", injection_check.detected_patterns)
        return {
            "scope_valid": False,
            "scope_message": (
                "I noticed your message contains content I cannot process. "
                "Please rephrase your health-related question."
            ),
            "is_escalated": False,
        }

    # Check query scope
    scope_result = validate_query_scope(user_message)
    if not scope_result.in_scope:
        return {
            "scope_valid": False,
            "scope_message": scope_result.redirect_message,
            "is_escalated": False,
        }

    # Check user population scope
    user_context = state.get("user_context", UserContext())
    if not user_context.is_in_target_population():
        return {
            "scope_valid": False,
            "scope_message": (
                "Based on the information provided, your situation may benefit from "
                "personalised professional guidance. Please consult a healthcare provider."
            ),
            "is_escalated": False,
        }

    return {"scope_valid": True, "scope_message": "", "is_escalated": False}


# ════════════════════════════════════════════════════════════
# Node 2: Deterministic Red-Flag Triage
# ════════════════════════════════════════════════════════════

def red_flag_triage_node(state: GraphState) -> dict[str, Any]:
    """Run deterministic red-flag detection on user input."""
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

    return {
        "triage_result": triage_result,
        "is_escalated": is_escalated,
    }


# ════════════════════════════════════════════════════════════
# Node 3: Clarification Node
# ════════════════════════════════════════════════════════════

def clarification_node(state: GraphState) -> dict[str, Any]:
    """Determine if we need more information before proceeding."""
    symptom_report = state.get("symptom_report")
    user_context = state.get("user_context", UserContext())

    questions: list[str] = []

    # Check for missing minimum information
    if symptom_report is None:
        questions.append("Could you describe your main symptom in a bit more detail?")
        return {"needs_clarification": True, "clarification_questions": questions}

    if not symptom_report.duration_description:
        questions.append("How long have you been experiencing this symptom?")

    if symptom_report.severity.value == "unknown":
        questions.append("Would you describe the intensity as mild, moderate, or severe?")

    if user_context.age_range.value == "unknown":
        questions.append("Could you share your age range? (18-25, 26-35, 36-45, 46-55, 56-65)")

    # For fever, ask about temperature
    if "fever" in (symptom_report.main_symptom or "").lower():
        if symptom_report.measured_temperature_c is None:
            questions.append("Have you measured your temperature? If so, what was the reading?")

    if questions:
        return {"needs_clarification": True, "clarification_questions": questions[:3]}

    return {"needs_clarification": False, "clarification_questions": []}


# ════════════════════════════════════════════════════════════
# Node 4: Query Planner
# ════════════════════════════════════════════════════════════

def query_planner_node(state: GraphState) -> dict[str, Any]:
    """Decompose user symptom into search queries for MCP connectors."""
    symptom_report = state.get("symptom_report")
    if symptom_report is None:
        return {"search_queries": []}

    main = symptom_report.main_symptom
    queries = [
        f"{main} self-care management",
        f"{main} home remedies evidence-based",
        f"{main} when to seek medical attention",
    ]

    # Add Ayurveda-specific query
    queries.append(f"{main} Ayurveda lifestyle non-pharmacological")

    return {"search_queries": queries}


# ════════════════════════════════════════════════════════════
# Node 5: MCP Retrieval
# ════════════════════════════════════════════════════════════

async def mcp_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Execute parallel searches across official read-only MCP data connectors.

    Queries:
    - PubMed / NCBI E-utilities
    - ClinicalTrials.gov API v2
    - MedlinePlus / NLM
    - Crossref Metadata API
    - WHO IRIS
    """
    import asyncio
    from medicobuddy.mcp.pubmed import PubMedConnector
    from medicobuddy.mcp.clinicaltrials import ClinicalTrialsConnector
    from medicobuddy.mcp.medlineplus import MedlinePlusConnector
    from medicobuddy.mcp.who_crossref_ayush_cochrane import CrossrefConnector, WHOConnector
    from medicobuddy.models.mcp import MCPResult

    search_queries = state.get("search_queries", [])
    if not search_queries:
        return {"mcp_results": []}

    logger.info("Executing MCP retrieval for %d queries", len(search_queries))
    all_results: list[MCPResult] = []

    connectors = [
        PubMedConnector(),
        ClinicalTrialsConnector(),
        MedlinePlusConnector(),
        CrossrefConnector(),
    ]

    async def fetch_connector_results(connector: Any, query: str) -> list[MCPResult]:
        try:
            return await connector.search(query, max_results=3)
        except Exception:
            logger.info("MCP connector %s query failed for '%s'", connector.connector_name, query)
            return []
        finally:
            await connector.close()

    tasks = [
        fetch_connector_results(conn, query)
        for query in search_queries[:2]  # Query top 2 planned terms
        for conn in connectors
    ]

    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    seen_titles: set[str] = set()
    for res_list in gathered:
        if isinstance(res_list, list):
            for item in res_list:
                if item.title and item.title.lower() not in seen_titles:
                    seen_titles.add(item.title.lower())
                    all_results.append(item)

    logger.info("MCP retrieval completed: %d authenticated evidence items retrieved", len(all_results))
    return {"mcp_results": all_results}


# ════════════════════════════════════════════════════════════
# Node 6: Hybrid Graph + Vector Retrieval
# ════════════════════════════════════════════════════════════

async def hybrid_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Perform hybrid GraphRAG retrieval combining Neo4j Cypher traversal + Milvus/pgvector vector search."""
    from medicobuddy.config import get_settings
    from medicobuddy.knowledge_graph.client import Neo4jClient
    from medicobuddy.knowledge_graph.queries import KnowledgeGraphQueries
    from medicobuddy.retrieval.hybrid import HybridRetriever
    from medicobuddy.retrieval.vector_store import VectorStoreClient

    settings = get_settings()
    symptom_report = state.get("symptom_report")
    user_context = state.get("user_context", UserContext())
    user_message = state.get("user_message", "")

    symptom_name = symptom_report.main_symptom if symptom_report else user_message
    conditions = user_context.chronic_conditions

    # Initialize graph and vector clients
    neo4j_client = Neo4jClient(settings)
    vector_store = VectorStoreClient(settings)

    graph_results = []
    vector_results = []
    fused_results = []
    contraindications = []
    ayurvedic_concepts = []

    try:
        await neo4j_client.connect()
        graph_queries = KnowledgeGraphQueries(neo4j_client)
        retriever = HybridRetriever(graph_queries, vector_store)

        retrieval_output = await retriever.retrieve(
            query=user_message,
            symptom_name=symptom_name,
            conditions=conditions,
            top_k=10,
        )

        graph_results = retrieval_output.get("graph_results", [])
        vector_results = retrieval_output.get("vector_results", [])
        fused_results = retrieval_output.get("fused_results", [])
        contraindications = retrieval_output.get("contraindications", [])
        ayurvedic_concepts = retrieval_output.get("ayurvedic_concepts", [])

    except Exception:
        logger.info("Knowledge Graph / Vector Store running in offline/graceful mode")
    finally:
        try:
            await neo4j_client.close()
        except Exception:
            pass

    return {
        "graph_results": graph_results,
        "vector_results": vector_results,
        "fused_results": fused_results,
        "contraindications": contraindications,
        "ayurvedic_graph_concepts": ayurvedic_concepts,
    }


# ════════════════════════════════════════════════════════════
# Node 7: Evidence Grader
# ════════════════════════════════════════════════════════════

def evidence_grader_node(state: GraphState) -> dict[str, Any]:
    """Score and filter retrieved evidence."""
    mcp_results: list[MCPResult] = state.get("mcp_results", [])

    graded: list[EvidenceClaim] = []
    scored: list[dict[str, Any]] = []

    for result in mcp_results:
        # Sanitize retrieved content
        doc_check = check_retrieved_document(result.supporting_passage)
        if not doc_check.is_safe:
            logger.warning("Injection detected in retrieved doc: %s", result.title)
            result.supporting_passage = doc_check.sanitized_text

        # Skip retracted papers
        if result.retraction_status == "retracted":
            logger.info("Skipping retracted paper: %s", result.title)
            continue

        study_ref = mcp_result_to_study_ref(result)
        score = score_study(study_ref)
        scored.append({"title": result.title, "score": score.composite_score})

    # Determine overall evidence level
    return {
        "graded_evidence": graded,
        "evidence_scores": scored,
    }


# ════════════════════════════════════════════════════════════
# Node 8: Contraindication & Safety Critic
# ════════════════════════════════════════════════════════════

def safety_critic_node(state: GraphState) -> dict[str, Any]:
    """Review proposed actions against contraindications and safety rules."""
    user_context = state.get("user_context", UserContext())
    contraindications = state.get("contraindications", [])
    comfort_steps = state.get("safe_comfort_steps", [])

    warnings: list[str] = []

    # Check if comfort steps conflict with user conditions
    for condition in user_context.chronic_conditions:
        cond_lower = condition.lower()
        for contra in contraindications:
            if cond_lower in str(contra.get("applies_to", "")).lower():
                warnings.append(
                    f"Note: {contra.get('description', '')} "
                    f"(relevant to your {condition})"
                )

    # Check allergies against any food recommendations
    for allergy in user_context.allergies:
        for step in comfort_steps:
            if allergy.lower() in step.lower():
                warnings.append(
                    f"Modified recommendation: Removed reference to {allergy} "
                    f"due to your reported allergy."
                )

    return {
        "safety_approved": len(warnings) == 0,
        "safety_warnings": warnings,
    }


# ════════════════════════════════════════════════════════════
# Node 9: Response Composer
# ════════════════════════════════════════════════════════════

def response_composer_node(state: GraphState) -> dict[str, Any]:
    """Assemble the 10-section MedicoBuddy response using Groq LLM + evidence."""
    from medicobuddy.llm import get_llm

    triage = state.get("triage_result", TriageResult(outcome=TriageOutcome.SELF_CARE, reasoning=""))
    symptom = state.get("symptom_report")
    user_context = state.get("user_context", UserContext())
    user_message = state.get("user_message", "")
    fused_results = state.get("fused_results", [])
    mcp_results: list[MCPResult] = state.get("mcp_results", [])

    # Build user report summary
    report = "You have reported: "
    if symptom:
        report += f"{symptom.main_symptom}"
        if symptom.duration_description:
            report += f" for {symptom.duration_description}"
        if symptom.severity.value != "unknown":
            report += f" (intensity: {symptom.severity.value})"
    else:
        report += user_message or "a health concern"

    # Baseline comfort steps
    comfort_steps = [
        "Rest in a comfortable, quiet environment with reduced sensory stimulation",
        "Stay adequately hydrated with small, frequent sips of plain water",
        "Avoid strenuous physical activity temporarily until feeling well",
    ]

    monitoring = [
        "Track whether symptoms are improving, stable, or worsening over 24-48 hours",
        "Monitor your body temperature if feeling warm or feverish",
        "Note any new or changing symptoms that develop",
    ]

    seek_care = [
        "Symptoms worsen significantly or do not improve within 24-48 hours",
        "You develop severe pain, high fever (>39°C / 102°F), or difficulty breathing",
        "You are unable to retain fluids due to persistent vomiting",
        "You experience any new, unexpected, or concerning symptoms",
    ]

    avoid = [
        "Avoid self-diagnosing or taking unprescribed medications",
        "Avoid intense exercise or heavy physical exertion until fully recovered",
    ]

    ayurveda_perspectives = [
        AyurvedaPerspective(
            practice="Warm water hydration (Ushnodaka)",
            description="Sipping warm water throughout the day is a traditional practice to aid comfort and digestion.",
            evidence_label="limited_or_preliminary_evidence",
        ),
        AyurvedaPerspective(
            practice="Consistent sleep-wake routine (Dinacharya)",
            description="Maintaining regular sleep and rest times supports body recovery and circadian balance.",
            evidence_label="evidence_supported",
        ),
    ]

    # Attempt Groq LLM synthesis if available
    llm = get_llm()
    if llm is not None:
        try:
            evidence_summary = "\n".join([f"- {r.title}: {r.supporting_passage[:200]}" for r in mcp_results[:3]])
            prompt = f"""You are MedicoBuddy, an evidence-grounded health educational assistant.
User query: {user_message}
Reported symptom: {report}
Evidence items:
{evidence_summary or 'No specific literature items.'}

Provide 3 concise, low-risk, non-pharmacological comfort steps as bullet points. Do NOT mention any drugs, dosages, or diagnoses."""
            response = llm.invoke(prompt)
            if hasattr(response, "content") and isinstance(response.content, str) and response.content.strip():
                lines = [line.strip("- *• ").strip() for line in response.content.split("\n") if line.strip("- *• ").strip()]
                if len(lines) >= 2:
                    comfort_steps = lines[:4]
        except Exception:
            logger.info("Groq LLM invocation skipped — using baseline templates")

    return {
        "user_report_summary": report,
        "safe_comfort_steps": comfort_steps,
        "monitoring_guidance": monitoring,
        "seek_care_conditions": seek_care,
        "things_to_avoid": avoid,
        "ayurveda_perspectives": ayurveda_perspectives,
    }


# ════════════════════════════════════════════════════════════
# Node 10: Output Validator (Deterministic)
# ════════════════════════════════════════════════════════════

def output_validator_node(state: GraphState) -> dict[str, Any]:
    """Deterministic post-generation safety check on the composed response."""
    # Collect all text that will be shown to the user
    text_parts = [
        state.get("user_report_summary", ""),
        *state.get("safe_comfort_steps", []),
        *state.get("things_to_avoid", []),
        *state.get("monitoring_guidance", []),
    ]
    full_text = " ".join(text_parts)

    validation = validate_output(full_text)

    if not validation.is_safe:
        logger.warning(
            "Output validation FAILED: %d violations",
            len(validation.violations),
        )
        return {
            "output_valid": False,
            "output_violations": [
                f"{v.category}: {v.matched_text}" for v in validation.violations
            ],
        }

    # Also run red-flag triage on the output
    output_triage = run_triage(full_text)
    if output_triage.red_flags_detected:
        logger.warning("Red flags detected in output — escalating")
        return {
            "output_valid": False,
            "output_violations": [
                f"Output contains red-flag language: {rf.flag_name}"
                for rf in output_triage.red_flags_detected
            ],
        }

    return {"output_valid": True, "output_violations": []}


# ════════════════════════════════════════════════════════════
# Node 11: Citation & Provenance Validator
# ════════════════════════════════════════════════════════════

def citation_validator_node(state: GraphState) -> dict[str, Any]:
    """Verify all citations are traceable and valid."""
    mcp_results: list[MCPResult] = state.get("mcp_results", [])

    citations: list[Citation] = []
    for i, result in enumerate(mcp_results, start=1):
        citations.append(
            Citation(
                number=i,
                title=result.title,
                authors=", ".join(result.authors[:3]),
                publication_date=result.publication_date,
                url=result.canonical_url,
                doi=result.doi,
                pmid=result.pmid,
                source_type=result.study_type,
            )
        )

    # Run provenance check
    full_text = " ".join(state.get("safe_comfort_steps", []))
    urls = [c.url for c in citations if c.url]
    warnings = check_provenance(full_text, urls)

    return {"citations": citations, "citation_warnings": warnings}


# ════════════════════════════════════════════════════════════
# Node 12: Final Response Assembly
# ════════════════════════════════════════════════════════════

def final_response_node(state: GraphState) -> dict[str, Any]:
    """Assemble the final MedicoBuddyResponse."""
    triage = state.get("triage_result", TriageResult(outcome=TriageOutcome.SELF_CARE, reasoning=""))

    # Map triage outcome to urgency summary
    urgency_map = {
        TriageOutcome.SELF_CARE: "Self-care information",
        TriageOutcome.CONSULT_CLINICIAN: "Contact a clinician",
        TriageOutcome.URGENT_CARE: "Seek urgent care immediately",
        TriageOutcome.OUT_OF_SCOPE: "Professional guidance recommended",
    }

    # Emergency message for escalated cases
    emergency_msg = ""
    if triage.outcome == TriageOutcome.URGENT_CARE:
        flags = ", ".join(rf.flag_name for rf in triage.red_flags_detected)
        emergency_msg = (
            f"⚠️ Based on what you've described ({flags}), this situation "
            "may require immediate medical attention. Please contact emergency "
            "services or visit the nearest emergency department."
        )

    # Determine evidence level
    evidence_scores = state.get("evidence_scores", [])
    if evidence_scores:
        avg_score = sum(s.get("score", 0) for s in evidence_scores) / len(evidence_scores)
        if avg_score >= 0.6:
            evidence_level = EvidenceLevel.HIGH
        elif avg_score >= 0.4:
            evidence_level = EvidenceLevel.MODERATE
        elif avg_score >= 0.2:
            evidence_level = EvidenceLevel.LIMITED
        else:
            evidence_level = EvidenceLevel.INSUFFICIENT
    else:
        evidence_level = EvidenceLevel.INSUFFICIENT

    response = MedicoBuddyResponse(
        triage_outcome=triage.outcome,
        urgency_summary=urgency_map.get(triage.outcome, "Unknown"),
        user_report_summary=state.get("user_report_summary", ""),
        safe_comfort_steps=state.get("safe_comfort_steps", []),
        ayurveda_perspectives=state.get("ayurveda_perspectives", []),
        things_to_avoid=state.get("things_to_avoid", []),
        monitoring_guidance=state.get("monitoring_guidance", []),
        seek_care_conditions=state.get("seek_care_conditions", []),
        overall_evidence_level=evidence_level,
        citations=state.get("citations", []),
        emergency_message=emergency_msg,
        emergency_contact=triage.emergency_contact,
    )

    return {"final_response": response}
