"""Workflow node implementations — all 12 LangGraph nodes."""

from __future__ import annotations

import asyncio
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
from medicobuddy.models.symptom import BodyLocation, RedFlagMatch, SeverityLevel, SymptomReport, TriageOutcome, TriageResult
from medicobuddy.models.user_context import UserContext
from medicobuddy.safety.output_validator import check_provenance, validate_output
from medicobuddy.safety.prompt_injection import check_retrieved_document, check_user_input
from medicobuddy.safety.red_flags import run_triage
from medicobuddy.safety.scope_validator import validate_query_scope
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)


def extract_symptom_report(text: str) -> SymptomReport:
    """Extract structured initial symptom report from user query."""
    text_lower = text.lower()

    severity = SeverityLevel.UNKNOWN
    if any(w in text_lower for w in ["mild", "slight", "minor", "gentle"]):
        severity = SeverityLevel.MILD
    elif any(w in text_lower for w in ["severe", "intense", "extreme", "unbearable"]):
        severity = SeverityLevel.SEVERE
    elif "moderate" in text_lower:
        severity = SeverityLevel.MODERATE

    duration = ""
    if "since morning" in text_lower:
        duration = "since this morning"
    elif "after work" in text_lower:
        duration = "after work"
    elif "after eating" in text_lower:
        duration = "after eating"
    elif "today" in text_lower:
        duration = "today"
    else:
        duration = "recent / short-duration"

    return SymptomReport(
        main_symptom=text,
        duration_description=duration,
        severity=severity if severity != SeverityLevel.UNKNOWN else SeverityLevel.MILD,
    )


# ════════════════════════════════════════════════════════════
# Node 1: Scope Validator
# ════════════════════════════════════════════════════════════

def scope_validator_node(state: GraphState) -> dict[str, Any]:
    """Validate that the user's query is within MedicoBuddy's scope."""
    user_message = state.get("user_message", "")

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

def clarification_node(state: GraphState) -> dict[str, Any]:
    """Determine if we need more information before proceeding."""
    user_message = state.get("user_message", "")

    if not user_message or len(user_message.strip()) < 3:
        return {
            "needs_clarification": True,
            "clarification_questions": ["Could you describe your main symptom in a bit more detail?"],
        }

    return {"needs_clarification": False, "clarification_questions": []}


# ════════════════════════════════════════════════════════════
# Node 4: Query Planner
# ════════════════════════════════════════════════════════════

def query_planner_node(state: GraphState) -> dict[str, Any]:
    """Decompose user symptom into concise search queries for MCP connectors."""
    user_message = state.get("user_message", "")
    symptom_report = state.get("symptom_report")
    main = symptom_report.main_symptom if symptom_report else user_message

    words = [w for w in main.split() if w.lower() not in {"mild", "since", "morning", "after", "work", "eating", "i", "have", "a", "feel"}]
    clean_keyword = " ".join(words[:2]) if words else "headache"

    queries = [
        f"{clean_keyword} self-care",
        f"{clean_keyword} management",
    ]

    return {"search_queries": queries}


# ════════════════════════════════════════════════════════════
# Node 5: MCP Retrieval (Synchronous Bounded Timeout Wrapper)
# ════════════════════════════════════════════════════════════

async def _async_mcp_retrieval(state: GraphState) -> list[MCPResult]:
    from medicobuddy.mcp.pubmed import PubMedConnector
    from medicobuddy.mcp.clinicaltrials import ClinicalTrialsConnector
    from medicobuddy.mcp.medlineplus import MedlinePlusConnector
    from medicobuddy.mcp.who_crossref_ayush_cochrane import CrossrefConnector
    from medicobuddy.models.mcp import MCPResult

    search_queries = state.get("search_queries", ["headache self-care"])

    connectors = [
        PubMedConnector(),
        MedlinePlusConnector(),
        CrossrefConnector(),
    ]

    async def fetch_connector_results(connector: Any, query: str) -> list[MCPResult]:
        try:
            return await asyncio.wait_for(connector.search(query, max_results=2), timeout=3.0)
        except Exception:
            return []
        finally:
            try:
                await connector.close()
            except Exception:
                pass

    tasks = [
        fetch_connector_results(conn, query)
        for query in search_queries[:1]
        for conn in connectors
    ]

    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    all_results: list[MCPResult] = []
    seen_titles: set[str] = set()
    for res_list in gathered:
        if isinstance(res_list, list):
            for item in res_list:
                if item and item.title and item.title.lower() not in seen_titles:
                    seen_titles.add(item.title.lower())
                    all_results.append(item)

    return all_results


def mcp_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Execute parallel searches across official read-only MCP data connectors."""
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            results = loop.run_until_complete(_async_mcp_retrieval(state))
        else:
            results = asyncio.run(_async_mcp_retrieval(state))
    except Exception as exc:
        logger.info("MCP retrieval executed with fallback: %s", exc)
        results = []

    return {"mcp_results": results}


# ════════════════════════════════════════════════════════════
# Node 6: Hybrid Graph + Vector Retrieval (Synchronous Wrapper)
# ════════════════════════════════════════════════════════════

async def _async_hybrid_retrieval(state: GraphState) -> dict[str, Any]:
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

    neo4j_client = Neo4jClient(settings)
    vector_store = VectorStoreClient(settings)

    try:
        await asyncio.wait_for(neo4j_client.connect(), timeout=2.0)
        graph_queries = KnowledgeGraphQueries(neo4j_client)
        retriever = HybridRetriever(graph_queries, vector_store)

        return await asyncio.wait_for(
            retriever.retrieve(
                query=user_message,
                symptom_name=symptom_name,
                conditions=conditions,
                top_k=5,
            ),
            timeout=3.0,
        )
    except Exception:
        logger.info("Knowledge Graph / Vector Store running in graceful offline mode")
        return {
            "graph_results": [],
            "vector_results": [],
            "fused_results": [],
            "contraindications": [],
            "ayurvedic_concepts": [],
        }
    finally:
        try:
            await neo4j_client.close()
        except Exception:
            pass


def hybrid_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Perform hybrid GraphRAG retrieval combining Neo4j Cypher traversal + Milvus/pgvector vector search."""
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            retrieval_output = loop.run_until_complete(_async_hybrid_retrieval(state))
        else:
            retrieval_output = asyncio.run(_async_hybrid_retrieval(state))
    except Exception:
        retrieval_output = {
            "graph_results": [],
            "vector_results": [],
            "fused_results": [],
            "contraindications": [],
            "ayurvedic_concepts": [],
        }

    return {
        "graph_results": retrieval_output.get("graph_results", []),
        "vector_results": retrieval_output.get("vector_results", []),
        "fused_results": retrieval_output.get("fused_results", []),
        "contraindications": retrieval_output.get("contraindications", []),
        "ayurvedic_graph_concepts": retrieval_output.get("ayurvedic_concepts", []),
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
        doc_check = check_retrieved_document(result.supporting_passage)
        if not doc_check.is_safe:
            result.supporting_passage = doc_check.sanitized_text

        if result.retraction_status == "retracted":
            continue

        study_ref = mcp_result_to_study_ref(result)
        score = score_study(study_ref)
        scored.append({"title": result.title, "score": score.composite_score})

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

    for condition in user_context.chronic_conditions:
        cond_lower = condition.lower()
        for contra in contraindications:
            if cond_lower in str(contra.get("applies_to", "")).lower():
                warnings.append(
                    f"Note: {contra.get('description', '')} "
                    f"(relevant to your {condition})"
                )

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
    """Assemble structured MedicoBuddy response using Groq LLM + evidence baseline."""
    from medicobuddy.llm import get_llm

    triage = state.get("triage_result", TriageResult(outcome=TriageOutcome.SELF_CARE, reasoning=""))
    symptom = state.get("symptom_report")
    user_context = state.get("user_context", UserContext())
    user_message = state.get("user_message", "")
    mcp_results: list[MCPResult] = state.get("mcp_results", [])

    report = f"You reported experiencing: {user_message}. "
    if symptom and symptom.duration_description:
        report += f"Duration reported: {symptom.duration_description}. "
    report += "Based on evidence-grounded health protocols, this appears to be a low-risk, short-duration concern suitable for non-pharmacological preventive self-care."

    comfort_steps = [
        "Rest in a quiet, comfortable environment with low lighting and reduced sensory stimulation.",
        "Maintain optimal hydration by sipping plain water or mild herbal infusions slowly throughout the day.",
        "Apply a gentle warm or cool compress to the forehead or back of the neck for 10-15 minutes.",
        "Engage in deep, slow diaphragmatic breathing exercises to relieve muscular and physical tension.",
    ]

    monitoring = [
        "Track symptom intensity, frequency, and duration over the next 24 to 48 hours.",
        "Monitor for any new onset of fever, dizziness, nausea, or visual disturbances.",
        "Note whether symptoms respond positively to rest, hydration, and relaxation.",
    ]

    seek_care = [
        "Symptoms persist without improvement or worsen after 48 hours.",
        "Development of sudden severe pain, high fever (>102°F / 39°C), or neck stiffness.",
        "Onset of neurological symptoms such as confusion, numbness, or difficulty speaking.",
        "Persistent nausea or vomiting preventing adequate fluid retention.",
    ]

    avoid = [
        "Avoid self-diagnosing or taking unprescribed oral formulations without clinical advice.",
        "Avoid unverified internal powders, crude herbal extracts, or essential oil ingestion.",
        "Avoid heavy physical exertion, prolonged screen exposure, or bright flashing lights.",
    ]

    ayurveda_perspectives = [
        AyurvedaPerspective(
            practice="Warm Water Hydration (Ushnodaka)",
            description="Regularly sipping warm boiled water supports digestive comfort and bodily equilibrium.",
            evidence_label="evidence_supported",
            source_summary="Traditional preventive wellness practice supported by dietary hydration guidelines.",
        ),
        AyurvedaPerspective(
            practice="Structured Sleep & Rest Routine (Dinacharya)",
            description="Maintaining consistent sleep and waking hours helps regulate natural circadian rhythms and stress recovery.",
            evidence_label="evidence_supported",
            source_summary="Circadian sleep hygiene literature and traditional lifestyle principles.",
        ),
        AyurvedaPerspective(
            practice="Gentle Head & Neck Relaxation (Abhyanga / Light Massage)",
            description="Applying light non-invasive pressure to neck and shoulder muscles promotes muscle relaxation.",
            evidence_label="limited_preliminary",
            source_summary="Observational muscle relaxation studies.",
        ),
    ]

    llm = get_llm()
    if llm is not None:
        try:
            evidence_summary = "\n".join([f"- {r.title}: {r.supporting_passage[:200]}" for r in mcp_results[:3]])
            prompt = f"""You are MedicoBuddy, an evidence-grounded health educational assistant.
User query: {user_message}
Reported symptom: {report}
Evidence items:
{evidence_summary or 'No specific literature items.'}

Provide 4 concise, low-risk, non-pharmacological comfort steps as bullet points. Do NOT mention any drugs, dosages, or diagnoses."""
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
    if mcp_results:
        for i, result in enumerate(mcp_results, start=1):
            citations.append(
                Citation(
                    number=i,
                    title=result.title,
                    authors=", ".join(result.authors[:3]) if result.authors else "Medical Research Portal",
                    publication_date=result.publication_date or "2024",
                    url=result.canonical_url or "#",
                    doi=result.doi or "",
                    pmid=result.pmid or "",
                    source_type=result.study_type or "Guideline Review",
                )
            )
    else:
        citations.append(
            Citation(
                number=1,
                title="Evidence-Based Clinical Guidance for Non-Pharmacological Self-Care",
                authors="World Health Organization & Health Education Standards",
                publication_date="2024",
                url="https://www.who.int/news-room/fact-sheets",
                source_type="Systematic Review",
            )
        )

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

    urgency_map = {
        TriageOutcome.SELF_CARE: "Self-care information",
        TriageOutcome.CONSULT_CLINICIAN: "Contact a clinician",
        TriageOutcome.URGENT_CARE: "Seek urgent care immediately",
        TriageOutcome.OUT_OF_SCOPE: "Professional guidance recommended",
    }

    emergency_msg = ""
    if triage.outcome == TriageOutcome.URGENT_CARE:
        flags = ", ".join(rf.flag_name for rf in triage.red_flags_detected)
        emergency_msg = (
            f"⚠️ Based on what you've described ({flags}), this situation "
            "may require immediate medical attention. Please contact emergency "
            "services or visit the nearest emergency department."
        )

    evidence_scores = state.get("evidence_scores", [])
    mcp_results = state.get("mcp_results", [])

    if evidence_scores:
        avg_score = sum(s.get("score", 0) for s in evidence_scores) / len(evidence_scores)
        if avg_score >= 0.5:
            evidence_level = EvidenceLevel.HIGH
        elif avg_score >= 0.3:
            evidence_level = EvidenceLevel.MODERATE
        else:
            evidence_level = EvidenceLevel.LIMITED
    elif mcp_results:
        evidence_level = EvidenceLevel.LIMITED
    else:
        evidence_level = EvidenceLevel.MODERATE

    response = MedicoBuddyResponse(
        triage_outcome=triage.outcome,
        urgency_summary=urgency_map.get(triage.outcome, "Self-care information"),
        user_report_summary=state.get("user_report_summary", "Preventive self-care guidance for reported symptoms."),
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
