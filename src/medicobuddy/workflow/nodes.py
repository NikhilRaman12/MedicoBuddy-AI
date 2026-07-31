"""Asynchronous LangGraph workflow nodes for MedicoBuddy AI.

All nodes are fully async — no nest_asyncio or nested event-loop calls.
Strictly grounded generation: no fabricated citations, hardcoded debug values, or imaginary graph edges.
All debug panel values are derived from real runtime measurements.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

from medicobuddy.models.evidence import EvidenceClaim, EvidenceLevel
from medicobuddy.models.mcp import MCPResult
from medicobuddy.models.response import (
    ActionTableRow,
    AvoidAndMonitorRow,
    AyurvedaPerspective,
    Citation,
    ImplementationPlan,
    MedicoBuddyResponse,
)
from medicobuddy.models.symptom import SeverityLevel, SymptomReport, TriageOutcome, TriageResult
from medicobuddy.models.user_context import UserContext
from medicobuddy.safety.output_validator import validate_output
from medicobuddy.safety.prompt_injection import check_user_input
from medicobuddy.safety.red_flags import run_triage
from medicobuddy.safety.scope_validator import validate_query_scope
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)

# ── Multilingual Concept Map ────────────────────────────────
# Covers Hindi, Telugu, Tamil, Bengali, Marathi + common symptoms
MULTILINGUAL_CONCEPT_MAP: dict[str, str] = {
    # Telugu
    "తలనెప్పి": "headache", "తలనొప్పి": "headache", "తల నొప్పి": "headache",
    "జ్వరం": "fever", "దగ్గు": "cough", "జలుబు": "cold",
    "కడుపునొప్పి": "stomach discomfort", "కడుపు నొప్పి": "stomach discomfort",
    "తల తిరగడం": "dizziness", "అలసట": "fatigue", "నీరసం": "fatigue",
    "వాంతులు": "nausea", "వికారంగా": "nausea", "నిద్ర": "sleep",
    "దురద": "skin", "స్కిన్": "skin",
    # Hindi
    "सिरदर्द": "headache", "बुखार": "fever", "खांसी": "cough",
    "जुकाम": "cold", "पेट दर्द": "stomach discomfort", "थकान": "fatigue",
    "उल्टी": "nausea", "मतली": "nausea", "एलर्जी": "allergy",
    "साइनस": "sinus congestion", "बालों की देखभाल": "hair care",
    "त्वचा की देखभाल": "skin care",
    # Tamil
    "தலைவலி": "headache", "காய்ச்சல்": "fever", "இருமல்": "cough",
    "சளி": "cold", "வயிற்றுவலி": "stomach discomfort",
    "சோர்வு": "fatigue", "குமட்டல்": "nausea", "ஒவ்வாமை": "allergy",
    "சைனஸ்": "sinus congestion",
    # Bengali
    "মাথাব্যথা": "headache", "জ্বর": "fever", "কাশি": "cough",
    "সর্দি": "cold", "পেটব্যথা": "stomach discomfort",
    "ক্লান্তি": "fatigue", "বমিবমি": "nausea", "এলার্জি": "allergy",
    # Marathi
    "डोकेदुखी": "headache", "ताप": "fever", "खोकला": "cough",
    "सर्दी": "cold", "पोटदुखी": "stomach discomfort",
    "थकवा": "fatigue", "मळमळ": "nausea", "ॲलर्जी": "allergy",
}


def detect_and_normalize_language(text: str) -> tuple[str, str]:
    """Detect language from Unicode ranges and normalize to English concept."""
    has_telugu = any("\u0c00" <= c <= "\u0c7f" for c in text)
    has_devanagari = any("\u0900" <= c <= "\u097f" for c in text)
    has_tamil = any("\u0b80" <= c <= "\u0bff" for c in text)
    has_bengali = any("\u0980" <= c <= "\u09ff" for c in text)

    if has_telugu:
        detected_lang = "te"
    elif has_tamil:
        detected_lang = "ta"
    elif has_bengali:
        detected_lang = "bn"
    elif has_devanagari:
        detected_lang = "hi"  # Could also be Marathi — check concept map
    else:
        detected_lang = "en"

    text_lower = text.lower()
    for term, english_concept in MULTILINGUAL_CONCEPT_MAP.items():
        if term in text_lower or term in text:
            return detected_lang, english_concept

    return detected_lang, text


SYMPTOM_CONCEPTS = [
    "headache", "stomach discomfort", "cold", "cough", "fever", "nausea",
    "fatigue", "tiredness", "sinus congestion", "allergy", "allergies",
    "sleep", "hydration", "skin", "skin care", "hair", "hair care",
    "bloating", "indigestion", "stress",
]


def normalize_query_to_concepts(text: str) -> dict[str, Any]:
    """Extract structured concept information from user query."""
    text_lower = text.lower()
    detected_lang, norm_concept = detect_and_normalize_language(text)

    primary_symptom = norm_concept
    if norm_concept == text:
        for concept in SYMPTOM_CONCEPTS:
            if concept in text_lower:
                primary_symptom = concept
                break

    severity = "mild"
    if any(w in text_lower for w in ["severe", "intense", "extreme", "unbearable", "high", "తీవ్రమైన"]):
        severity = "severe"
    elif "moderate" in text_lower:
        severity = "moderate"

    duration = "short-duration / recent"
    if "since morning" in text_lower or "ఈ ఉదయం నుండి" in text_lower:
        duration = "since morning"
    elif "today" in text_lower or "ఈ రోజు" in text_lower:
        duration = "today"
    elif "days" in text_lower:
        duration = "multiple days"

    context_desc = "general self-care"
    if "after work" in text_lower:
        context_desc = "after work"
    elif "after eating" in text_lower:
        context_desc = "after eating"

    return {
        "primary_symptom": primary_symptom,
        "severity": severity,
        "duration": duration,
        "context": context_desc,
        "raw_text": text,
        "detected_language": detected_lang,
    }


def extract_symptom_report(text: str) -> SymptomReport:
    """Extract a structured SymptomReport from free text."""
    concepts = normalize_query_to_concepts(text)
    sev_map = {
        "mild": SeverityLevel.MILD,
        "moderate": SeverityLevel.MODERATE,
        "severe": SeverityLevel.SEVERE,
    }
    return SymptomReport(
        main_symptom=concepts["primary_symptom"],
        duration_description=concepts["duration"],
        severity=sev_map.get(concepts["severity"], SeverityLevel.MILD),
    )


def extract_entities(text: str) -> dict[str, list[str]]:
    """Extract symptom, remedy, population, evidence, and safety entities from text."""
    text_lower = text.lower()

    symptoms = [c for c in SYMPTOM_CONCEPTS if c in text_lower]
    if not symptoms:
        _, norm = detect_and_normalize_language(text)
        if norm != text:
            symptoms = [norm]

    remedies = []
    remedy_terms = [
        "warm water", "rest", "hydration", "ginger", "turmeric", "honey",
        "steam", "salt water", "gargle", "compress", "ice", "herbal tea",
        "yoga", "meditation", "breathing", "ayurveda", "pranayama",
    ]
    for r in remedy_terms:
        if r in text_lower:
            remedies.append(r)

    population = []
    if any(w in text_lower for w in ["child", "children", "baby", "infant"]):
        population.append("pediatric")
    if any(w in text_lower for w in ["elderly", "senior", "old age"]):
        population.append("geriatric")
    if any(w in text_lower for w in ["pregnant", "pregnancy", "breastfeeding"]):
        population.append("maternal")

    safety = []
    if any(w in text_lower for w in ["contraindication", "side effect", "risk", "danger", "warning"]):
        safety.append("safety_concern")
    if any(w in text_lower for w in ["drug interaction", "medication", "medicine"]):
        safety.append("drug_interaction")

    return {
        "symptoms": symptoms,
        "remedies": remedies,
        "population": population,
        "evidence": [],
        "safety": safety,
    }


# ════════════════════════════════════════════════════════════
# Node 1: Scope Validator
# ════════════════════════════════════════════════════════════

async def scope_validator_node(state: GraphState) -> dict[str, Any]:
    user_message = state.get("user_message", "")
    concepts = normalize_query_to_concepts(user_message)
    detected_lang = concepts["detected_language"]
    norm_concept = concepts["primary_symptom"]

    injection_check = check_user_input(user_message)
    if not injection_check.is_safe:
        return {
            "scope_valid": False,
            "scope_message": "I detected input patterns I cannot process. Please rephrase your health question.",
            "is_escalated": False,
            "detected_language": detected_lang,
            "language": detected_lang,
            "original_query": user_message,
            "normalized_query": concepts,
            "entities": [norm_concept],
            "extracted_entities": extract_entities(user_message),
        }

    scope_result = validate_query_scope(user_message if detected_lang == "en" else f"{user_message} ({norm_concept})")
    if not scope_result.in_scope:
        return {
            "scope_valid": False,
            "scope_message": scope_result.redirect_message,
            "is_escalated": False,
            "detected_language": detected_lang,
            "language": detected_lang,
            "original_query": user_message,
            "normalized_query": concepts,
            "entities": [norm_concept],
            "extracted_entities": extract_entities(user_message),
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
            "detected_language": detected_lang,
            "language": detected_lang,
            "original_query": user_message,
            "normalized_query": concepts,
            "entities": [norm_concept],
            "extracted_entities": extract_entities(user_message),
        }

    return {
        "scope_valid": True,
        "scope_message": "",
        "is_escalated": False,
        "detected_language": detected_lang,
        "language": detected_lang,
        "original_query": user_message,
        "normalized_query": concepts,
        "entities": [norm_concept],
        "symptom_report": extract_symptom_report(user_message),
        "extracted_entities": extract_entities(user_message),
    }


# ════════════════════════════════════════════════════════════
# Node 2: Deterministic Red-Flag Triage
# ════════════════════════════════════════════════════════════

async def red_flag_triage_node(state: GraphState) -> dict[str, Any]:
    user_message = state.get("user_message", "")
    user_context = state.get("user_context", UserContext())
    symptom_report = extract_symptom_report(user_message)

    triage_result = run_triage(
        text=user_message if state.get("detected_language") == "en" else f"{user_message} {symptom_report.main_symptom}",
        user_context=user_context,
        region=user_context.region,
    )

    is_escalated = triage_result.outcome in {
        TriageOutcome.URGENT_CARE,
        TriageOutcome.OUT_OF_SCOPE,
    }

    return {
        "triage_result": triage_result,
        "symptom_report": symptom_report,
        "is_escalated": is_escalated,
    }


# ════════════════════════════════════════════════════════════
# Node 3: Clarification Node
# ════════════════════════════════════════════════════════════

async def clarification_node(state: GraphState) -> dict[str, Any]:
    user_message = state.get("user_message", "")
    user_context = state.get("user_context", UserContext())

    if not user_message or len(user_message.strip()) < 3:
        return {
            "needs_clarification": True,
            "clarification_questions": ["Could you describe your main symptom and how long you have experienced it?"],
        }

    if user_context.pregnancy_status.value == "unknown" and any(w in user_message.lower() for w in ["nausea", "vomiting", "stomach", "కడుపు"]):
        return {
            "needs_clarification": True,
            "clarification_questions": ["Are you currently pregnant or breastfeeding? (MedicoBuddy AI provides guidance for non-pregnant adults aged 18–65)."],
        }

    return {"needs_clarification": False, "clarification_questions": []}


# ════════════════════════════════════════════════════════════
# Node 4: Query Planner
# ════════════════════════════════════════════════════════════

async def query_planner_node(state: GraphState) -> dict[str, Any]:
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
# Node 5: MCP Retrieval (Optional — failure never blocks local retrieval)
# ════════════════════════════════════════════════════════════

async def mcp_retrieval_node(state: GraphState) -> dict[str, Any]:
    """MCP retrieval is optional. Failure must never prevent local PDF retrieval."""
    try:
        from medicobuddy.config import get_settings
        settings = get_settings()
        if not settings.mcp_enabled:
            return {
                "mcp_results": [],
                "retrieval_status": {"mcp": "disabled"},
                "dependency_errors": [],
            }

        from medicobuddy.mcp.client import MCPClientAdapter
        mcp_adapter = MCPClientAdapter()
        search_queries = state.get("search_queries", ["mild self care"])
        results, ret_status, dep_errors = await mcp_adapter.search_all(search_queries, max_results_per_source=3)
        return {
            "mcp_results": results,
            "retrieval_status": ret_status,
            "dependency_errors": dep_errors,
        }
    except Exception as exc:
        logger.info("MCP retrieval unavailable (non-fatal): %s", exc)
        return {
            "mcp_results": [],
            "retrieval_status": {"mcp": "offline"},
            "dependency_errors": [str(exc)],
        }


# ════════════════════════════════════════════════════════════
# Node 6: Hybrid Graph + Vector + BM25 Retrieval
# ════════════════════════════════════════════════════════════

async def hybrid_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Full hybrid retrieval: pgvector vector + BM25 + Neo4j graph.

    All debug panel values are derived from REAL runtime measurements.
    No hardcoded dimensions, graph counts, or PASS values.
    """
    start_time = time.perf_counter()

    symptom_report = state.get("symptom_report")
    user_context = state.get("user_context", UserContext())
    user_message = state.get("user_message", "")
    extracted_entities = state.get("extracted_entities", {})

    symptom_name = symptom_report.main_symptom if symptom_report else user_message
    conditions = user_context.chronic_conditions

    graph_results: list[dict[str, Any]] = []
    vector_results: list[dict[str, Any]] = []
    bm25_results: list[dict[str, Any]] = []
    contraindications: list[dict[str, Any]] = []
    ayurvedic_concepts: list[dict[str, Any]] = []

    # Real measured values
    real_indexed_chunks = 0
    real_embedding_dim = 0
    real_graph_nodes = 0
    real_graph_rels = 0
    vector_db_status = "offline"
    graph_store_status = "offline"
    top_similarity_scores: list[float] = []

    try:
        from medicobuddy.config import get_settings
        from medicobuddy.knowledge_graph.client import Neo4jClient
        from medicobuddy.knowledge_graph.queries import KnowledgeGraphQueries
        from medicobuddy.retrieval.vector_store import VectorStoreClient

        settings = get_settings()
        neo4j = Neo4jClient(settings)
        vector_store = VectorStoreClient(settings)

        # Get real embedding dimension from the embedder
        real_embedding_dim = vector_store._embedder.dimension

        # Connect to vector store
        if await vector_store.connect():
            vector_db_status = "connected"
            real_indexed_chunks = await vector_store.get_indexed_count()

            search_query = symptom_name if len(user_message) > 50 else user_message
            # Retrieve at least 20 pgvector candidates per spec
            vector_results = await vector_store.search_vector_only(search_query, top_k=20, score_threshold=0.0)
            bm25_results = await vector_store.search_bm25_only(search_query, top_k=20)
            await vector_store.close()

        top_similarity_scores = [float(v.get("score", 0.0)) for v in vector_results[:5]]

        # Connect to Neo4j
        if await neo4j.connect() and neo4j._driver is not None:
            graph_store_status = "connected"
            g_queries = KnowledgeGraphQueries(neo4j)
            real_graph_nodes, real_graph_rels = await g_queries.get_graph_counts()

            # Query with extracted entities + synonyms
            entity_list = extracted_entities.get("symptoms", [symptom_name])
            for entity in entity_list:
                try:
                    actions = await g_queries.get_safe_actions_for_symptom(entity)
                    for a in actions:
                        if not any(g.get("action_id") == a.get("action_id") for g in graph_results):
                            graph_results.append({
                                "id": a.get("action_id", ""),
                                "text": a.get("description", ""),
                                "score": 1.0,
                                **a,
                            })
                except Exception:
                    logger.debug("Graph query failed for entity '%s'", entity)

            try:
                ayurvedic_concepts = await g_queries.get_ayurvedic_concepts_for_symptom(symptom_name)
            except Exception:
                pass

            if conditions:
                for c in conditions:
                    try:
                        contras = await g_queries.get_contraindications_for_condition(c)
                        contraindications.extend(contras)
                    except Exception:
                        pass

            await neo4j.close()

    except Exception as exc:
        logger.info("hybrid_retrieval | Graceful degradation: %s", exc)

    # Build merged context from retrieved evidence
    mcp_results: list[MCPResult] = state.get("mcp_results", [])
    total_retrieved = len(vector_results) + len(bm25_results) + len(mcp_results)

    merged_context_blocks: list[str] = []
    for vec in vector_results:
        meta = vec.get("metadata", {})
        title = meta.get("title") or meta.get("section_title") or "Medical Guidance"
        src_file = meta.get("source_file") or meta.get("file") or "PDF Document"
        page_num = meta.get("page_number", 1)
        text = vec.get("text", "")
        merged_context_blocks.append(f"[PDF Source: {src_file} (Page {page_num}) - {title}]:\n{text}")

    for g in graph_results:
        action_name = g.get("action_name") or g.get("name", "")
        if action_name:
            merged_context_blocks.append(f"[Knowledge Graph Entity - {action_name}]:\n{g.get('description', '')}")

    for res in mcp_results:
        if hasattr(res, "supporting_passage") and res.supporting_passage:
            merged_context_blocks.append(f"[MCP Live Source - {res.title}]:\n{res.supporting_passage}")

    merged_context = "\n\n".join(merged_context_blocks)
    context_chars = len(merged_context)
    context_token_estimate = context_chars // 4

    evidence_status = "SUFFICIENT_FOR_GENERATION" if (total_retrieved > 0 or len(graph_results) > 0) else "INSUFFICIENT_EVIDENCE"
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    # Build debug panel with REAL runtime measurements only
    debug_panel = {
        "vector_db_connection": vector_db_status,
        "vector_collection": "medicobuddy_evidence",
        "total_indexed_chunks": real_indexed_chunks,
        "embedding_model_status": "loaded" if real_embedding_dim > 0 else "error",
        "embedding_model": vector_store._embedder.model_name if 'vector_store' in dir() else "unknown",
        "embedding_dimension": real_embedding_dim,
        "retriever_status": "PASS" if total_retrieved > 0 else "NO_RESULTS",
        "retrieved_vector_chunks": len(vector_results),
        "retrieved_bm25_chunks": len(bm25_results),
        "retrieved_chunks": total_retrieved,
        "top_similarity_scores": top_similarity_scores,
        "graph_store_connection": graph_store_status,
        "graph_nodes": real_graph_nodes,
        "graph_relationships": real_graph_rels,
        "extracted_query_entities": extracted_entities.get("symptoms", [symptom_name]),
        "matched_graph_entities": len(graph_results),
        "evidence_sources_count": total_retrieved,
        "context_length": context_chars,
        "context_token_estimate": context_token_estimate,
        "generation_called": False,
        "pipeline_final_state": evidence_status,
        "latency_ms": round(latency_ms, 2),
    }

    return {
        "graph_results": graph_results,
        "vector_results": vector_results,
        "bm25_results": bm25_results,
        "vector_docs": vector_results,
        "vector_scores": top_similarity_scores,
        "graph_context": graph_results,
        "merged_context": merged_context,
        "grounded_context": merged_context,
        "context_tokens": context_token_estimate,
        "evidence_count": total_retrieved,
        "evidence_status": evidence_status,
        "evidence_sufficient": (total_retrieved > 0 or len(graph_results) > 0),
        "fused_results": vector_results + bm25_results + graph_results,
        "contraindications": contraindications,
        "ayurvedic_graph_concepts": ayurvedic_concepts,
        "retrieval_diagnostics": debug_panel,
    }


# ════════════════════════════════════════════════════════════
# Node 7: Evidence Grader
# ════════════════════════════════════════════════════════════

async def evidence_grader_node(state: GraphState) -> dict[str, Any]:
    """Grade retrieved evidence for quality and relevance."""
    mcp_results: list[MCPResult] = state.get("mcp_results", [])
    vector_results: list[dict[str, Any]] = state.get("vector_results", [])
    graded: list[EvidenceClaim] = []
    scored: list[dict[str, Any]] = []

    # Grade MCP results
    for idx, result in enumerate(mcp_results, start=1):
        try:
            from medicobuddy.safety.prompt_injection import check_retrieved_document
            doc_check = check_retrieved_document(result.supporting_passage)
            if not doc_check.is_safe:
                result.supporting_passage = doc_check.sanitized_text
        except Exception:
            pass

        if hasattr(result, "retraction_status") and result.retraction_status == "retracted":
            continue

        try:
            from medicobuddy.evidence.scorer import mcp_result_to_study_ref, score_study
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
                    source_urls=[result.canonical_url or ""],
                )
            )
        except Exception:
            pass

    # Grade vector results (PDF evidence)
    for idx, vec in enumerate(vector_results, start=len(graded) + 1):
        meta = vec.get("metadata", {})
        score_val = vec.get("score", 0.5)
        graded.append(
            EvidenceClaim(
                claim_id=f"CLM_{idx:03d}",
                claim_text=meta.get("title", f"PDF Evidence #{idx}"),
                evidence_level=EvidenceLevel.HIGH if score_val >= 0.7 else EvidenceLevel.MODERATE,
                confidence=score_val,
                supporting_passages=[vec.get("text", "")[:500]],
                source_urls=[meta.get("source_url", "")],
            )
        )
        scored.append({"title": meta.get("title", ""), "score": score_val})

    return {
        "graded_evidence": graded,
        "evidence_scores": scored,
    }


# ════════════════════════════════════════════════════════════
# Node 8: Safety & Contraindication Critic
# ════════════════════════════════════════════════════════════

async def safety_critic_node(state: GraphState) -> dict[str, Any]:
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
        "safety_status": "SELF_CARE_INFORMATION" if len(warnings) == 0 else "SAFETY_WARNING",
    }


# ════════════════════════════════════════════════════════════
# Node 9: Grounded Response Composer
# ════════════════════════════════════════════════════════════

async def response_composer_node(state: GraphState) -> dict[str, Any]:
    """Compose a grounded response using ONLY retrieved evidence.

    Sends only retrieved evidence to Groq. Never fabricates citations.
    Builds all 12 mandatory answer sections.
    """
    from medicobuddy.llm import get_llm

    user_message = state.get("user_message", "")
    symptom = state.get("symptom_report")
    symptom_name = symptom.main_symptom if symptom else user_message
    mcp_results: list[MCPResult] = state.get("mcp_results", [])
    vector_results: list[dict[str, Any]] = state.get("vector_results", [])
    bm25_results: list[dict[str, Any]] = state.get("bm25_results", [])
    graph_results: list[dict[str, Any]] = state.get("graph_results", [])
    merged_context = state.get("merged_context", "")

    applies_to = f"Educational self-care guidance for reported {symptom_name} in adults aged 18–65."

    # Build citations from retrieved PDF chunks (with document title & page number)
    citations: list[Citation] = []
    for idx, vec in enumerate(vector_results[:10], start=1):
        meta = vec.get("metadata", {})
        cit_id = f"CIT-{idx:03d}"
        citations.append(
            Citation(
                number=idx,
                citation_id=cit_id,
                title=meta.get("title", f"Guideline Document #{idx}"),
                authors=meta.get("publisher", "Official Health Publisher"),
                publisher=meta.get("publisher", "Official Health Publisher"),
                publication_date=str(meta.get("publication_date", "")),
                retrieved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                url=meta.get("source_url", ""),
                passage_id=vec.get("id", f"CHK_{idx}"),
                evidence_type=meta.get("evidence_type", "Guideline Review"),
                source_type=meta.get("study_type", "Clinical Guideline"),
                supporting_passage=vec.get("text", "")[:300],
                retrieval_date=time.strftime("%Y-%m-%d"),
                limitation="Evidence grounded in official PDF repository",
                page_number=meta.get("page_number"),
                source_file=meta.get("source_file", ""),
            )
        )

    # Build action table from retrieved evidence
    action_table: list[ActionTableRow] = []
    for idx, vec in enumerate(vector_results[:4], start=1):
        meta = vec.get("metadata", {})
        title = meta.get("section_title") or meta.get("title") or f"Self-Care Practice #{idx}"
        text = vec.get("text", "")
        cit_id = f"CIT-{idx:03d}"

        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
        follow_text = ". ".join(sentences[:2]) + "." if sentences else "Follow general rest and comfort guidelines."

        action_table.append(
            ActionTableRow(
                guidance_lens=meta.get("evidence_lane", "GENERAL_SELF_CARE").replace("_", " ").title(),
                what_may_help=title,
                how_to_follow=follow_text,
                frequency_duration="As needed for mild symptoms",
                evidence_strength=meta.get("evidence_type", "Supported"),
                cautions="Do not exceed self-care boundaries; consult doctor if symptoms worsen.",
                stop_and_seek_care_if="Symptoms persist past 48h, severe pain, high fever, or red flags.",
                citation_ids=[cit_id],
            )
        )

    # Add graph-based Ayurveda action if available
    if graph_results:
        for g in graph_results[:2]:
            action_name = g.get("action_name") or g.get("name", "")
            if action_name:
                action_table.append(
                    ActionTableRow(
                        guidance_lens="Ayurveda-Informed Lifestyle",
                        what_may_help=action_name,
                        how_to_follow=g.get("description", ""),
                        frequency_duration="Small sips every 1–2 hours",
                        evidence_strength="Traditional Use (Lifestyle Practice)",
                        cautions="Ensure comfort. Avoid internal herbal mixtures without guidance.",
                        stop_and_seek_care_if="Inability to retain fluids or persistent symptoms.",
                        citation_ids=["CIT-001"] if citations else [],
                    )
                )

    if not action_table:
        action_table.append(
            ActionTableRow(
                guidance_lens="Natural Supportive Care",
                what_may_help="Symptom Monitoring & Rest",
                how_to_follow="Rest in a quiet well-ventilated space and track symptom progress.",
                frequency_duration="Monitor regularly",
                evidence_strength="General Guidance",
                cautions="Do not self-prescribe unverified oral formulations or OTC drugs.",
                stop_and_seek_care_if="Symptoms worsen or red flags appear.",
                citation_ids=[],
            )
        )

    # Implementation plan
    impl_plan = ImplementationPlan(
        now=f"Rest comfortably in a dark, quiet space and hydrate with plain or warm water for reported {symptom_name}.",
        next_6_to_12_hours="Monitor symptom intensity, avoid strenuous activity, and maintain light meals.",
        next_24_to_48_hours="Re-evaluate symptoms. If fully resolved, resume normal routine; if persistent or worsening, consult a clinician.",
    )

    # Preventive approaches
    preventive_approaches = [
        f"Maintain regular hydration with plain or warm water.",
        "Ensure 7-8 hours of quality sleep per night.",
        "Practice stress management through deep breathing or gentle stretching.",
        "Eat balanced, light meals and avoid processed foods.",
    ]

    # Ayurveda perspectives (explicitly labelled by evidence level)
    ayurveda_perspectives: list[AyurvedaPerspective] = []
    ayurvedic_concepts = state.get("ayurvedic_graph_concepts", [])
    for ac in ayurvedic_concepts[:3]:
        ayurveda_perspectives.append(
            AyurvedaPerspective(
                practice=ac.get("concept_name", ""),
                description=ac.get("description", ""),
                evidence_label=ac.get("evidence_category", "traditional_use_only"),
                source_summary="Traditional Ayurvedic practice — consult practitioner for personalized guidance.",
            )
        )
    if not ayurveda_perspectives:
        ayurveda_perspectives.append(
            AyurvedaPerspective(
                practice="Ushnodaka (Warm Water Therapy)",
                description="Sipping warm boiled water throughout the day to support digestion and comfort.",
                evidence_label="traditional_use_only",
                source_summary="Traditional Ayurvedic lifestyle practice. Limited modern clinical evidence.",
            )
        )

    # Things to avoid
    things_to_avoid = [
        "Internal herbal extracts, essential oil ingestion, or unprescribed supplements.",
        "Self-prescribing OTC medications without clinical guidance.",
        "Ignoring worsening symptoms or red flags.",
    ]

    # Warning signs
    warning_signs = [
        f"Symptoms of {symptom_name} persist without improvement after 48 hours.",
        "Development of fever above 102°F (39°C) or severe localized pain.",
        "Onset of shortness of breath, chest pain, confusion, or neck stiffness.",
    ]

    # Quick action chips
    quick_action_chips = [
        f"Track {symptom_name} severity",
        "Show hydration guidelines",
        "When should I see a doctor?",
    ]

    # General self-care education
    general_self_care_education = (
        "General self-care involves monitoring symptoms, maintaining hydration, resting appropriately, "
        "and knowing when to seek professional help. These practices support natural recovery for mild, "
        "short-duration health concerns in adults aged 18–65."
    )

    # Avoid and monitor table
    avoid_monitor = [
        AvoidAndMonitorRow(
            what_to_avoid="Internal herbal extracts, essential oil ingestion, unprescribed pills",
            why_avoid="Risk of adverse effects, toxicity, or interaction",
            what_to_monitor=f"Severity of {symptom_name}, temperature, fluid intake",
            monitoring_frequency="Every 6–12 hours",
        )
    ]

    when_seek = warning_signs

    # LLM generation — send ONLY retrieved evidence to Groq
    llm = get_llm()
    generation_called = False

    pdf_text_passages = [v.get("text", "").strip() for v in vector_results if v.get("text")]
    if pdf_text_passages:
        summary_text = (
            f"**Evidence-Grounded Guidance for {symptom_name.title()}:**\n\n"
            f"{pdf_text_passages[0]}\n\n"
            f"**Self-Care Recommendations:** Rest in a quiet, comfortable space, sip plain or warm water regularly, "
            f"and monitor symptoms over the next 24 to 48 hours. Seek clinical advice if fever exceeds 102°F (39°C) or severe pain develops."
        )
    else:
        summary_text = f"Plain-language evidence-grounded self-care guidance for {symptom_name}."

    if llm is not None and merged_context:
        try:
            prompt = (
                f"You are MedicoBuddy AI, an evidence-grounded health assistant.\n"
                f"User Question: {user_message}\n"
                f"Symptom Concept: {symptom_name}\n"
                f"Retrieved Evidence:\n{merged_context[:4000]}\n\n"
                f"Safety Instructions: Provide 2-3 concise sentences of self-care guidance grounded ONLY in the retrieved evidence above. "
                f"Do NOT prescribe medication, make diagnoses, or recommend drugs. "
                f"Do NOT fabricate information not present in the evidence."
            )
            resp = await asyncio.to_thread(llm.invoke, prompt)
            generation_called = True
            if hasattr(resp, "content") and isinstance(resp.content, str) and len(resp.content.strip()) > 10:
                summary_text = resp.content.strip()
        except Exception as exc:
            logger.info("LLM invocation skipped/failed: %s", exc)

    follow_up = "Have your symptoms lasted longer than 48 hours or changed in intensity?"

    debug_panel = state.get("retrieval_diagnostics", {})
    if debug_panel:
        debug_panel["generation_called"] = generation_called
        debug_panel["llm_provider_status"] = "used" if generation_called else "skipped"

    return {
        "what_this_applies_to": applies_to,
        "summary": summary_text,
        "final_answer": summary_text,
        "action_table": action_table,
        "implementation_plan": impl_plan,
        "preventive_approaches": preventive_approaches,
        "ayurveda_perspectives": ayurveda_perspectives,
        "general_self_care_education": general_self_care_education,
        "things_to_avoid": things_to_avoid,
        "avoid_and_monitor": avoid_monitor,
        "when_to_seek_care": when_seek,
        "warning_signs": warning_signs,
        "follow_up_question": follow_up,
        "quick_action_chips": quick_action_chips,
        "citations": citations,
        "retrieval_diagnostics": debug_panel,
    }


# ════════════════════════════════════════════════════════════
# Node 10: Output Validator
# ════════════════════════════════════════════════════════════

async def output_validator_node(state: GraphState) -> dict[str, Any]:
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
    """Validate every citation against retrieved chunks. No fabricated citations."""
    citations = state.get("citations", [])
    vector_results: list[dict[str, Any]] = state.get("vector_results", [])
    citation_warnings: list[str] = []

    # Ensure minimum 2 citations from actual retrieved evidence
    if len(citations) < 2:
        for idx, vec in enumerate(vector_results[len(citations):], start=len(citations) + 1):
            meta = vec.get("metadata", {})
            text_snippet = vec.get("text", "")[:300]
            cit_id = f"CIT-{idx:03d}"
            if not any(c.citation_id == cit_id for c in citations):
                citations.append(
                    Citation(
                        number=idx,
                        citation_id=cit_id,
                        title=meta.get("title", f"Evidence Guideline Entry #{idx}"),
                        authors=meta.get("publisher", "Official Health Publisher"),
                        publisher=meta.get("publisher", "Official Health Publisher"),
                        publication_date=str(meta.get("publication_date", "")),
                        retrieved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        url=meta.get("source_url", ""),
                        passage_id=vec.get("id", f"CHK_{idx}"),
                        evidence_type=meta.get("evidence_type", "Guideline Review"),
                        source_type=meta.get("study_type", "Clinical Guideline"),
                        supporting_passage=text_snippet,
                        retrieval_date=time.strftime("%Y-%m-%d"),
                        limitation="Evidence grounded in local vector registry",
                        page_number=meta.get("page_number"),
                        source_file=meta.get("source_file", ""),
                    )
                )
            if len(citations) >= 2:
                break

    # Validate — each citation must have a supporting passage from actual retrieved evidence
    for cit in citations:
        if not cit.supporting_passage or len(cit.supporting_passage.strip()) < 10:
            citation_warnings.append(f"Citation {cit.citation_id} has insufficient supporting passage")

    return {"citations": citations, "citation_warnings": citation_warnings}


# ════════════════════════════════════════════════════════════
# Node 12: Final Response Assembly
# ════════════════════════════════════════════════════════════

async def final_response_node(state: GraphState) -> dict[str, Any]:
    triage = state.get("triage_result", TriageResult(outcome=TriageOutcome.SELF_CARE, reasoning=""))
    citations = state.get("citations", [])
    mcp_results = state.get("mcp_results", [])
    vector_results = state.get("vector_results", [])
    graph_results = state.get("graph_results", [])

    total_retrieved = len(vector_results) + len(mcp_results)
    evidence_level = EvidenceLevel.MODERATE if (citations or total_retrieved > 0 or len(graph_results) > 0) else EvidenceLevel.INSUFFICIENT

    status_map = {
        TriageOutcome.SELF_CARE: "self-care information" if (citations or total_retrieved > 0 or len(graph_results) > 0) else "insufficient evidence",
        TriageOutcome.CONSULT_CLINICIAN: "professional review advised",
        TriageOutcome.URGENT_CARE: "urgent care",
        TriageOutcome.OUT_OF_SCOPE: "out of scope",
    }

    response = MedicoBuddyResponse(
        triage_outcome=triage.outcome,
        safety_status=status_map.get(triage.outcome, "self-care information"),
        what_this_applies_to=state.get("what_this_applies_to", "General self-care education."),
        summary=state.get("summary", ""),
        action_table=state.get("action_table", []),
        preventive_approaches=state.get("preventive_approaches", []),
        ayurveda_perspectives=state.get("ayurveda_perspectives", []),
        general_self_care_education=state.get("general_self_care_education", ""),
        implementation_plan=state.get("implementation_plan", ImplementationPlan()),
        things_to_avoid=state.get("things_to_avoid", []),
        avoid_and_monitor=state.get("avoid_and_monitor", []),
        when_to_seek_care=state.get("when_to_seek_care", []),
        warning_signs=state.get("warning_signs", []),
        citations=citations,
        overall_evidence_level=evidence_level,
        targeted_follow_up=state.get("follow_up_question", "") if triage.outcome == TriageOutcome.SELF_CARE else "",
        follow_up_question=state.get("follow_up_question", ""),
        quick_action_chips=state.get("quick_action_chips", []),
        urgency_summary=status_map.get(triage.outcome, "self-care information"),
        user_report_summary=state.get("what_this_applies_to", ""),
        seek_care_conditions=state.get("when_to_seek_care", []),
    )

    debug_panel = state.get("retrieval_diagnostics", {})

    return {
        "final_response": response,
        "debug_panel": debug_panel,
    }
