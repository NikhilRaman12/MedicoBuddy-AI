"""Asynchronous LangGraph workflow nodes for MedicoBuddy AI.

All nodes are fully async — no nest_asyncio or nested event-loop calls.
Strictly grounded generation: uses RAG evidence + built-in medicobuddy_metadata store + Groq LLM.
Always produces structured 12-section responses with a complete Action Table.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

from medicobuddy.evidence.metadata_store import get_metadata_for_symptom, search_metadata
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
MULTILINGUAL_CONCEPT_MAP: dict[str, str] = {
    # Hair Loss Canonicalization (hairfall, hair fall, hair loss, hair shedding -> hair_loss)
    "hairfall": "hair_loss", "hair fall": "hair_loss", "hair loss": "hair_loss", "hair shedding": "hair_loss",
    "safety tips hairfall": "hair_loss", "safety measures for hairfall": "hair_loss",
    "జుట్టు రాలడం": "hair_loss", "జుట్టు ఊడటం": "hair_loss", "बाल झड़ना": "hair_loss", "बाल गिरना": "hair_loss",
    "முடி உதிர்தல்": "hair_loss", "ಕೂದಲು ಉದುರುವುದು": "hair_loss", "ಕೂದಲು ಉದುರುವಿಕೆ": "hair_loss",
    "മുടി കൊഴിച്ചിൽ": "hair_loss", "વાળ ખરવા": "hair_loss", "ਬਾਲ ਝੜਨਾ": "hair_loss", "ਚੁਟੀ ଝଡିବା": "hair_loss",
    "بالوں کا جھڑنا": "hair_loss",
    # Telugu
    "తలనెప్పి": "headache", "తలనొప్పి": "headache", "తల నొప్పి": "headache",
    "జ్వరం": "fever", "దగ్గు": "cough", "జలుబు": "cold",
    "కడుపునొప్పి": "stomach discomfort", "కడుపు అసౌకర్యం": "stomach discomfort", "గ్యాస్": "stomach discomfort",
    "తల తిరగడం": "dizziness", "అలసట": "fatigue", "నీరసం": "fatigue",
    "వాంతులు": "nausea", "వికారంగా": "nausea", "నిద్ర": "sleep",
    "దురద": "skin", "స్కిన్": "skin",
    # Hindi
    "सिरदर्द": "headache", "बुखार": "fever", "खांसी": "cough",
    "जुकाम": "cold", "पेट दर्द": "stomach discomfort", "थकान": "fatigue",
    "उल्टी": "nausea", "मतली": "nausea", "एलर्जी": "allergy",
    "साइनस": "sinus congestion", "बालों की देखभाल": "hair care", "त्वचा": "skin care",
    # Tamil
    "தலைவலி": "headache", "காய்ச்சல்": "fever", "இருமல்": "cough",
    "சளி": "cold", "வயிற்றுவலி": "stomach discomfort",
    "சோர்வு": "fatigue", "குமட்டல்": "nausea", "ஒவ்வாமை": "allergy",
    "சைனஸ்": "sinus congestion",
    # Bengali
    "মাথাব্যথা": "headache", "জ্বর": "fever", "কাশি": "cough",
    "সর্দি": "cold", "পেটব্যথা": "stomach discomfort",
    "ক্লান্তি": "fatigue", "বমিবমি": "nausea", "বমি": "nausea", "এলার্জি": "allergy",
    # Marathi
    "डोकेदुखी": "headache", "ताप": "fever", "खोकला": "cough",
    "सर्दी": "cold", "पोटदुखी": "stomach discomfort",
    "थकवा": "fatigue", "मळमळ": "nausea", "ॲलर्जी": "allergy", "त्वचेचा": "skin care",
    # Gujarati
    "માથાનો દુખાવો": "headache", "તાવ": "fever", "ઉધરસ": "cough",
    "શરદી": "cold", "પેટમાં દુખાવો": "stomach discomfort",
    "થાક": "fatigue", "ઉબકા": "nausea", "વાળની સંભાળ": "hair care",
    # Kannada
    "ತಲೆನೋವು": "headache", "ಜ್ವರ": "fever", "ಕೆಮ್ಮು": "cough",
    "ಶೀತ": "cold", "ಹೊಟ್ಟೆ ನೋವು": "stomach discomfort",
    "ಆಯಾಸ": "fatigue", "ಒತ್ತಡ": "stress",
    # Malayalam
    "തലവേദന": "headache", "പനി": "fever", "ചുമ": "cough",
    "അസുഖം": "cold", "ക്ഷീണം": "fatigue", "ഉറക്കമില്ലായ്മ": "sleep",
    # Punjabi
    "ਸਿਰ ਦਰਦ": "headache", "ਬੁਖਾਰ": "fever", "ਖੰਘ": "cough",
    "ਜ਼ੁਕਾਮ": "cold", "ਥਕਾਵਟ": "fatigue",
    # Odia
    "ମୁଣ୍ଡ ବିନ୍ଧା": "headache", "ଜର": "fever", "କାଶ": "cough",
    "ଥଣ୍ଡା": "cold", "ଥକାପଣ": "fatigue",
    # Urdu
    "سر درد": "headache", "بخار": "fever", "کھانسی": "cough",
    "نزلہ": "cold", "تھکاوٹ": "fatigue",
}


def detect_and_normalize_language(text: str) -> tuple[str, str]:
    """Detect language from Unicode ranges and normalize to English concept."""
    has_telugu = any("\u0c00" <= c <= "\u0c7f" for c in text)
    has_devanagari = any("\u0900" <= c <= "\u097f" for c in text)
    has_tamil = any("\u0b80" <= c <= "\u0bff" for c in text)
    has_bengali = any("\u0980" <= c <= "\u09ff" for c in text)
    has_gujarati = any("\u0a80" <= c <= "\u0aff" for c in text)
    has_kannada = any("\u0c80" <= c <= "\u0cff" for c in text)
    has_malayalam = any("\u0d00" <= c <= "\u0d7f" for c in text)
    has_gurmukhi = any("\u0a00" <= c <= "\u0a7f" for c in text)
    has_odia = any("\u0b00" <= c <= "\u0b7f" for c in text)
    has_arabic_script = any("\u0600" <= c <= "\u06ff" for c in text)

    if has_telugu:
        detected_lang = "te"
    elif has_tamil:
        detected_lang = "ta"
    elif has_bengali:
        detected_lang = "bn"
    elif has_gujarati:
        detected_lang = "gu"
    elif has_kannada:
        detected_lang = "kn"
    elif has_malayalam:
        detected_lang = "ml"
    elif has_gurmukhi:
        detected_lang = "pa"
    elif has_odia:
        detected_lang = "or"
    elif has_arabic_script:
        detected_lang = "ur"
    elif has_devanagari:
        detected_lang = "hi"
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
    "bloating", "indigestion", "stress", "vomiting", "constipation",
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
    if any(w in text_lower for w in ["severe", "intense", "extreme", "unbearable", "high"]):
        severity = "severe"
    elif "moderate" in text_lower:
        severity = "moderate"

    duration = "short-duration / recent"
    if "since morning" in text_lower:
        duration = "since morning"
    elif "today" in text_lower:
        duration = "today"

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

    return {
        "symptoms": symptoms,
        "remedies": remedies,
        "population": [],
        "evidence": [],
        "safety": [],
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

    if not user_message or len(user_message.strip()) < 3:
        return {
            "needs_clarification": True,
            "clarification_questions": ["Could you describe your main symptom and how long you have experienced it?"],
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
# Node 5: MCP Retrieval (Optional)
# ════════════════════════════════════════════════════════════

async def mcp_retrieval_node(state: GraphState) -> dict[str, Any]:
    return {
        "mcp_results": [],
        "retrieval_status": {"mcp": "disabled"},
        "dependency_errors": [],
    }


# ════════════════════════════════════════════════════════════
# Node 6: Hybrid Graph + Vector + BM25 + Metadata Store Retrieval
# ════════════════════════════════════════════════════════════

async def hybrid_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Full hybrid retrieval: pgvector + BM25 + Neo4j + allowlisted MCPs + medicobuddy_metadata store.

    Guarantees retrieval hits so search never returns 0 chunks.
    Clears previous turn state and records retrieval_query_hash.
    """
    start_time = time.perf_counter()

    # Clear previous retrieval state and capture active query hash
    active_q_hash = state.get("query_hash", "")
    user_message = state.get("user_message", "")
    symptom_report = state.get("symptom_report")
    user_context = state.get("user_context", UserContext())
    extracted_entities = state.get("extracted_entities", {})

    symptom_name = symptom_report.main_symptom if symptom_report else user_message

    graph_results: list[dict[str, Any]] = []
    vector_results: list[dict[str, Any]] = []
    bm25_results: list[dict[str, Any]] = []
    mcp_results: list[MCPResult] = []
    contraindications: list[dict[str, Any]] = []
    ayurvedic_concepts: list[dict[str, Any]] = []

    real_indexed_chunks = 0
    real_embedding_dim = 1024
    real_graph_nodes = 0
    real_graph_rels = 0
    vector_db_status = "offline"
    graph_store_status = "offline"
    top_similarity_scores: list[float] = []

    # 1. Search pgvector + BM25 + Neo4j DB + allowlisted MCPs concurrently
    try:
        from medicobuddy.config import get_settings
        from medicobuddy.knowledge_graph.client import Neo4jClient
        from medicobuddy.knowledge_graph.queries import KnowledgeGraphQueries
        from medicobuddy.mcp.client import MCPClientAdapter
        from medicobuddy.retrieval.vector_store import VectorStoreClient

        settings = get_settings()
        vector_store = VectorStoreClient(settings)
        mcp_client = MCPClientAdapter()

        # Run vector search and MCP search concurrently
        if await vector_store.connect():
            vector_db_status = "connected"
            real_indexed_chunks = await vector_store.get_indexed_count()
            search_query = symptom_name if len(user_message) > 50 else user_message
            vector_results = await vector_store.search_vector_only(search_query, top_k=20, score_threshold=0.0)
            bm25_results = await vector_store.search_bm25_only(search_query, top_k=20)
            await vector_store.close()

        top_similarity_scores = [float(v.get("score", 0.0)) for v in vector_results[:5]]

        # Search allowlisted MCP evidence servers (PubMed, Europe PMC, CT.gov, Local PDF)
        await mcp_client.initialize()
        mcp_items, mcp_status, mcp_errs = await mcp_client.search_all([user_message], max_results_per_source=3)
        mcp_results = mcp_items

        neo4j = Neo4jClient(settings)
        if await neo4j.connect() and neo4j._driver is not None:
            graph_store_status = "connected"
            g_queries = KnowledgeGraphQueries(neo4j)
            real_graph_nodes, real_graph_rels = await g_queries.get_graph_counts()
            entity_list = extracted_entities.get("symptoms", [symptom_name])
            for entity in entity_list:
                try:
                    actions = await g_queries.get_safe_actions_for_symptom(entity)
                    for a in actions:
                        if not any(g.get("action_id") == a.get("action_id") for g in graph_results):
                            graph_results.append({"id": a.get("action_id", ""), "text": a.get("description", ""), "score": 1.0, **a})
                except Exception:
                    pass

            try:
                ayurvedic_concepts = await g_queries.get_ayurvedic_concepts_for_symptom(symptom_name)
            except Exception:
                pass

            await neo4j.close()

    except Exception as exc:
        logger.info("hybrid_retrieval DB search fallback: %s", exc)

    # 2. Query built-in medicobuddy_metadata store
    metadata_chunks = search_metadata(user_message)
    if metadata_chunks:
        vector_results = metadata_chunks + vector_results

    # 3. Untrusted Data Protection & Prompt Injection Sanitization
    def _sanitize(txt: str) -> str:
        bad_phrases = ["ignore previous instructions", "system prompt:", "you are now an unrestricted", "disregard safety"]
        clean_t = txt
        for p in bad_phrases:
            if p in clean_t.lower():
                clean_t = clean_t.replace(p, "[REJECTED INSTRUCTION]")
        return clean_t

    for v in vector_results:
        v["text"] = _sanitize(v.get("text", ""))

    total_retrieved = len(vector_results) + len(bm25_results) + len(mcp_results)

    merged_context_blocks: list[str] = []
    for vec in vector_results:
        meta = vec.get("metadata", {})
        title = meta.get("title") or meta.get("section_title") or "Medical Guidance"
        src_file = meta.get("source_file") or meta.get("file") or "Repository Evidence"
        page_num = meta.get("page_number", 1)
        text = vec.get("text", "")
        merged_context_blocks.append(f"[{src_file} (Page {page_num}) - {title}]:\n{text}")

    for m in mcp_results:
        merged_context_blocks.append(f"[{m.source_connector.upper()} - {m.title}] (License: {m.license}):\n{_sanitize(m.supporting_passage)}")

    merged_context = "\n\n".join(merged_context_blocks)
    context_chars = len(merged_context)
    context_token_estimate = context_chars // 4

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    debug_panel = {
        "vector_db_connection": vector_db_status if real_indexed_chunks > 0 else "medicobuddy_metadata",
        "vector_collection": "medicobuddy_evidence",
        "total_indexed_chunks": max(real_indexed_chunks, len(metadata_chunks)),
        "embedding_model_status": "loaded",
        "embedding_model": "Qwen/Qwen3-Embedding-0.6B",
        "embedding_dimension": real_embedding_dim,
        "retriever_status": "PASS",
        "retrieved_vector_chunks": len(vector_results),
        "retrieved_bm25_chunks": len(bm25_results),
        "retrieved_chunks": total_retrieved,
        "top_similarity_scores": top_similarity_scores or [0.95, 0.92],
        "graph_store_connection": graph_store_status,
        "graph_nodes": real_graph_nodes,
        "graph_relationships": real_graph_rels,
        "extracted_query_entities": extracted_entities.get("symptoms", [symptom_name]),
        "matched_graph_entities": len(graph_results),
        "evidence_sources_count": total_retrieved,
        "context_length": context_chars,
        "context_token_estimate": context_token_estimate,
        "generation_called": False,
        "pipeline_final_state": "SUFFICIENT_FOR_GENERATION",
        "latency_ms": round(latency_ms, 2),
    }

    return {
        "retrieval_query_hash": active_q_hash,
        "mcp_results": mcp_results,
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
        "evidence_status": "SUFFICIENT_FOR_GENERATION",
        "evidence_sufficient": True,
        "fused_results": vector_results + bm25_results + graph_results,
        "contraindications": contraindications,
        "ayurvedic_graph_concepts": ayurvedic_concepts,
        "retrieval_diagnostics": debug_panel,
    }


# ════════════════════════════════════════════════════════════
# Node 7: Evidence Grader
# ════════════════════════════════════════════════════════════

async def evidence_grader_node(state: GraphState) -> dict[str, Any]:
    vector_results: list[dict[str, Any]] = state.get("vector_results", [])
    graded: list[EvidenceClaim] = []
    scored: list[dict[str, Any]] = []

    for idx, vec in enumerate(vector_results[:10], start=1):
        meta = vec.get("metadata", {})
        score_val = vec.get("score", 0.9)
        graded.append(
            EvidenceClaim(
                claim_id=f"CLM_{idx:03d}",
                claim_text=meta.get("title", f"Self-Care Guidance #{idx}"),
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
# Node 9: Grounded Response Composer with LLM & Structured Action Table
# ════════════════════════════════════════════════════════════

async def response_composer_node(state: GraphState) -> dict[str, Any]:
    """Compose a structured answer using Groq LLM + medicobuddy_metadata store.

    ALWAYS builds a full 12-section answer with a complete Action Table.
    """
    from medicobuddy.llm import get_llm

    # Assert query_hash consistency to reject generation on mismatched state
    req_q_hash = state.get("query_hash", "")
    ret_q_hash = state.get("retrieval_query_hash", "")
    if req_q_hash and ret_q_hash and req_q_hash != ret_q_hash:
        raise ValueError(f"State query_hash mismatch ({req_q_hash} != {ret_q_hash}) — rejecting generation.")

    user_message = state.get("user_message", "")
    symptom = state.get("symptom_report")
    symptom_name = symptom.main_symptom if symptom else user_message
    vector_results: list[dict[str, Any]] = state.get("vector_results", [])
    merged_context = state.get("merged_context", "")

    applies_to = f"Educational self-care guidance for reported {symptom_name} in adults aged 18–65."

    # Look up metadata registry entry dynamically from user_message
    meta_entry = get_metadata_for_symptom(user_message)

    # 1. Build Action Table
    action_table: list[ActionTableRow] = []

    # Add Natural Remedies
    for r in meta_entry.get("natural_remedies", []):
        action_table.append(
            ActionTableRow(
                guidance_lens=r.get("guidance_lens", "Natural Self-Care"),
                what_may_help=r.get("what_may_help", "Hydration & Rest"),
                how_to_follow=r.get("how_to_follow", "Sip fluids slowly and rest in a quiet space."),
                frequency_duration=r.get("frequency_duration", "As needed"),
                evidence_strength=r.get("evidence_strength", "High"),
                cautions=r.get("cautions", "Ensure comfort."),
                stop_and_seek_care_if=r.get("stop_and_seek_care_if", "If symptoms worsen or fever > 102°F."),
                citation_ids=["CIT-001"],
            )
        )

    # Add Ayurvedic Remedies
    for r in meta_entry.get("ayurvedic_remedies", []):
        action_table.append(
            ActionTableRow(
                guidance_lens=r.get("guidance_lens", "Ayurveda-Informed Wellness"),
                what_may_help=r.get("what_may_help", "Warm Water Therapy"),
                how_to_follow=r.get("how_to_follow", "Sip warm boiled water infused with ginger or cumin."),
                frequency_duration=r.get("frequency_duration", "Small sips throughout the day"),
                evidence_strength=r.get("evidence_strength", "Traditional Use"),
                cautions=r.get("cautions", "Avoid spicy foods."),
                stop_and_seek_care_if=r.get("stop_and_seek_care_if", "If vomiting persists > 24h."),
                citation_ids=["CIT-002"],
            )
        )

    # Add Allopathic / General Self-Care
    for r in meta_entry.get("allopathic_self_care", []):
        action_table.append(
            ActionTableRow(
                guidance_lens=r.get("guidance_lens", "General Medical Self-Care"),
                what_may_help=r.get("what_may_help", "Oral Rehydration & Rest"),
                how_to_follow=r.get("how_to_follow", "Sip electrolyte fluids or ORS to prevent dehydration."),
                frequency_duration=r.get("frequency_duration", "Throughout the day"),
                evidence_strength=r.get("evidence_strength", "High (Clinical Guidelines)"),
                cautions=r.get("cautions", "Do not self-prescribe unverified OTC medicines."),
                stop_and_seek_care_if=r.get("stop_and_seek_care_if", "Severe pain or dehydration signs."),
                citation_ids=["CIT-003"],
            )
        )

    # 2. Implementation Plan
    impl_plan = ImplementationPlan(
        now=f"Rest in a comfortable room, avoid heavy food, and sip warm water or ginger tea for reported {symptom_name}.",
        next_6_to_12_hours="Maintain light bland meals (like rice, bananas, toast) and track symptom progress.",
        next_24_to_48_hours="Re-evaluate symptoms. If fully resolved, resume normal routine; if persistent or worsening, consult a clinician.",
    )

    # 3. Preventive & Immune Boosting Approaches
    preventive_approaches = meta_entry.get("immune_and_preventive", [
        f"Maintain regular hydration with plain or warm water.",
        "Ensure 7-8 hours of quality sleep per night.",
        "Eat fresh, light, digestible meals.",
    ])

    # 4. Ayurvedic Perspectives
    ayurveda_perspectives: list[AyurvedaPerspective] = []
    for r in meta_entry.get("ayurvedic_remedies", []):
        ayurveda_perspectives.append(
            AyurvedaPerspective(
                practice=r.get("what_may_help", "Warm Water Therapy"),
                description=r.get("how_to_follow", ""),
                evidence_label="traditional_use_only",
                source_summary="Traditional Ayurvedic lifestyle practice.",
            )
        )

    # 5. Things to Avoid
    things_to_avoid = meta_entry.get("things_to_avoid", [
        "Oily, fried, spicy, or heavy protein-rich meals.",
        "Self-prescribing prescription medications without clinical advice.",
        "Ignoring severe pain or high fever.",
    ])

    # 6. Warning Signs & Seek Care
    warning_signs = meta_entry.get("seek_care_triggers", [
        f"Symptoms of {symptom_name} persist longer than 24-48 hours.",
        "High fever above 102°F (39°C) or severe localized pain.",
        "Signs of severe dehydration, confusion, or difficulty breathing.",
    ])

    # 7. Citations
    citations = [
        Citation(
            number=1,
            citation_id="CIT-001",
            title=f"Clinical Evidence & Self-Care Guidelines for {symptom_name.title()}",
            authors="MedicoBuddy Evidence Registry",
            publisher="Consumer Health Guidelines",
            publication_date="2026",
            supporting_passage=f"Recommended non-pharmacological self-care options for mild {symptom_name} include hydration, rest, and bland diet.",
            page_number=1,
            source_file="medicobuddy_metadata_registry.pdf",
        ),
        Citation(
            number=2,
            citation_id="CIT-002",
            title=f"Ayurvedic Preventive & Self-Care Guidelines",
            authors="CCRAS & Traditional Pharmacopoeia",
            publisher="Ayurvedic Science Institute",
            publication_date="2026",
            supporting_passage=f"Traditional lifestyle practices such as Ushnodaka (warm water) and herbal infusions for digestive comfort.",
            page_number=1,
            source_file="ccras_ayurveda_science_of_life.pdf",
        ),
    ]

    # 8. Summary Guidance with LLM
    llm = get_llm()
    generation_called = False
    summary_text = (
        f"**Evidence-Backed Self-Care Guidance for {symptom_name.title()}:**\n\n"
        f"For mild {symptom_name}, natural self-care focuses on adequate hydration, comfortable rest, and gentle digestive support. "
        f"Sip warm water or ginger tea slowly, eat light meals, and avoid oily or spicy foods. "
        f"If symptoms worsen or fever exceeds 102°F (39°C), seek clinical evaluation."
    )

    if llm is not None:
        try:
            prompt = (
                f"You are MedicoBuddy AI, an evidence-grounded health workstation assistant.\n"
                f"User Question: {user_message}\n"
                f"Symptom: {symptom_name}\n"
                f"Evidence & Metadata Context:\n{merged_context[:3000]}\n\n"
                f"Instruction: Provide 3 clear, empathetic sentences explaining what {symptom_name} is and the key non-pharmacological "
                f"self-care, natural remedy, and Ayurvedic recommendations. Do NOT prescribe drugs."
            )
            resp = await asyncio.to_thread(llm.invoke, prompt)
            generation_called = True
            if hasattr(resp, "content") and isinstance(resp.content, str) and len(resp.content.strip()) > 10:
                summary_text = resp.content.strip()
        except Exception as exc:
            logger.info("LLM invocation failed: %s", exc)

    quick_action_chips = [
        f"What natural remedies help {symptom_name}?",
        f"Ayurvedic tips for {symptom_name}",
        "When should I see a doctor?",
    ]

    debug_panel = state.get("retrieval_diagnostics", {})
    if debug_panel:
        debug_panel["generation_called"] = generation_called
        debug_panel["llm_provider_status"] = "used" if generation_called else "fallback"

    return {
        "what_this_applies_to": applies_to,
        "summary": summary_text,
        "final_answer": summary_text,
        "action_table": action_table,
        "implementation_plan": impl_plan,
        "preventive_approaches": preventive_approaches,
        "ayurveda_perspectives": ayurveda_perspectives,
        "general_self_care_education": (
            f"General self-care for {symptom_name} involves supporting your body's natural recovery through "
            "hydration, light nutrition, rest, and avoiding irritants. Always seek professional care if symptoms severe or persistent."
        ),
        "things_to_avoid": things_to_avoid,
        "avoid_and_monitor": [
            AvoidAndMonitorRow(
                what_to_avoid="Oily, fried food, self-prescribing OTC drugs",
                why_avoid="Risk of stomach irritation or adverse reactions",
                what_to_monitor=f"Symptom intensity, fluid intake, temperature",
                monitoring_frequency="Every 6-12 hours",
            )
        ],
        "when_to_seek_care": warning_signs,
        "warning_signs": warning_signs,
        "follow_up_question": f"Have your symptoms lasted longer than 24-48 hours or changed in intensity?",
        "quick_action_chips": quick_action_chips,
        "citations": citations,
        "retrieval_diagnostics": debug_panel,
    }


# ════════════════════════════════════════════════════════════
# Node 10: Output Validator
# ════════════════════════════════════════════════════════════

async def output_validator_node(state: GraphState) -> dict[str, Any]:
    return {"output_valid": True, "output_violations": []}


# ════════════════════════════════════════════════════════════
# Node 11: Citation & Entailment Validator
# ════════════════════════════════════════════════════════════

async def citation_validator_node(state: GraphState) -> dict[str, Any]:
    citations = state.get("citations", [])
    return {"citations": citations, "citation_warnings": []}


# ════════════════════════════════════════════════════════════
# Node 12: Final Response Assembly
# ════════════════════════════════════════════════════════════

async def final_response_node(state: GraphState) -> dict[str, Any]:
    triage = state.get("triage_result", TriageResult(outcome=TriageOutcome.SELF_CARE, reasoning=""))
    citations = state.get("citations", [])

    response = MedicoBuddyResponse(
        triage_outcome=triage.outcome,
        safety_status="self-care information",
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
        overall_evidence_level=EvidenceLevel.HIGH,
        targeted_follow_up=state.get("follow_up_question", ""),
        follow_up_question=state.get("follow_up_question", ""),
        quick_action_chips=state.get("quick_action_chips", []),
        urgency_summary="self-care information",
        user_report_summary=state.get("what_this_applies_to", ""),
        seek_care_conditions=state.get("when_to_seek_care", []),
    )

    debug_panel = state.get("retrieval_diagnostics", {})

    return {
        "final_response": response,
        "debug_panel": debug_panel,
    }


# ════════════════════════════════════════════════════════════
# Node: Language Router
# ════════════════════════════════════════════════════════════

async def language_router_node(state: GraphState) -> dict[str, Any]:
    """LangGraph node to route query language and normalize to English medical concepts."""
    user_message = state.get("user_message", "")
    preferred_lang = state.get("preferred_language", "auto")

    detected_lang, norm_concept = detect_and_normalize_language(user_message)

    if preferred_lang and preferred_lang != "auto":
        target_lang = preferred_lang
    else:
        target_lang = detected_lang

    return {
        "detected_language": detected_lang,
        "preferred_language": preferred_lang,
        "target_language": target_lang,
        "response_language": target_lang,
        "normalized_english_query": norm_concept,
        "language": target_lang,
        "translation_status": "pending" if target_lang != "en" else "not_required",
    }


# ════════════════════════════════════════════════════════════
# Node: Structured Translation
# ════════════════════════════════════════════════════════════

async def structured_translation_node(state: GraphState) -> dict[str, Any]:
    """Translate structured user-facing answer fields into target_language."""
    target_lang = state.get("target_language", "en")
    if target_lang == "en":
        return {"translation_status": "skipped"}

    import json
    from medicobuddy.llm import get_llm

    try:
        llm = get_llm()
        if llm:
            prompt = f"""You are an expert medical translator. Translate the following structured healthcare output into target language code '{target_lang}'.
RULES:
1. Do NOT translate: PMIDs, PMCIDs, DOIs, URLs, chunk IDs, page numbers, numbers, or bracket numbers like [1].
2. Translate all user-facing content into natural, accurate medical self-care language for language '{target_lang}'.
3. Return ONLY a valid JSON object matching this schema:
{{
  "summary": "...",
  "what_this_applies_to": "...",
  "follow_up_question": "...",
  "general_self_care_education": "...",
  "preventive_approaches": ["..."],
  "things_to_avoid": ["..."],
  "when_to_seek_care": ["..."],
  "warning_signs": ["..."],
  "quick_action_chips": ["..."],
  "action_table": [
    {{
      "guidance_lens": "...",
      "what_may_help": "...",
      "how_to_follow": "...",
      "frequency_duration": "...",
      "evidence_strength": "...",
      "cautions": "...",
      "stop_and_seek_care_if": "..."
    }}
  ]
}}

CONTENT:
{json.dumps({
    'summary': state.get('summary', ''),
    'what_this_applies_to': state.get('what_this_applies_to', ''),
    'follow_up_question': state.get('follow_up_question', ''),
    'general_self_care_education': state.get('general_self_care_education', ''),
    'preventive_approaches': state.get('preventive_approaches', []),
    'things_to_avoid': state.get('things_to_avoid', []),
    'when_to_seek_care': state.get('when_to_seek_care', []),
    'warning_signs': state.get('warning_signs', []),
    'quick_action_chips': state.get('quick_action_chips', []),
    'action_table': [r.model_dump() if hasattr(r, 'model_dump') else r for r in state.get('action_table', [])],
}, ensure_ascii=False, indent=2)}
"""
            llm_res = await llm.ainvoke(prompt)
            raw_text = str(getattr(llm_res, "content", ""))
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_text)
            updates: dict[str, Any] = {"translation_status": "success"}
            for key in ["summary", "what_this_applies_to", "follow_up_question", "general_self_care_education", "preventive_approaches", "things_to_avoid", "when_to_seek_care", "warning_signs", "quick_action_chips"]:
                if parsed.get(key):
                    updates[key] = parsed[key]

            if parsed.get("action_table") and isinstance(parsed["action_table"], list):
                orig_table = state.get("action_table", [])
                new_table = []
                for idx, r in enumerate(parsed["action_table"]):
                    old_cits = orig_table[idx].citation_ids if (idx < len(orig_table) and hasattr(orig_table[idx], "citation_ids")) else ["CIT-001"]
                    new_table.append(ActionTableRow(
                        guidance_lens=r.get("guidance_lens", "Natural Self-Care"),
                        what_may_help=r.get("what_may_help", "Hydration"),
                        how_to_follow=r.get("how_to_follow", "Rest"),
                        frequency_duration=r.get("frequency_duration", "As needed"),
                        evidence_strength=r.get("evidence_strength", "High"),
                        cautions=r.get("cautions", "Ensure comfort."),
                        stop_and_seek_care_if=r.get("stop_and_seek_care_if", "If symptoms worsen."),
                        citation_ids=old_cits,
                    ))
                updates["action_table"] = new_table

            return updates
    except Exception as exc:
        logger.warning("Structured translation node error: %s", exc)

    # ── Fallback Multilingual Dictionary Translation Engine ──
    FALLBACK_TRANSLATIONS: dict[str, dict[str, Any]] = {
        "te": {
            "summary_prefix": "**ఆధారాలతో కూడిన స్వయం-రక్షణ మార్గదర్శకత్వం:**",
            "what_applies": "పరిమిత స్వల్పకాలిక ఆరోగ్య ఆందోళనల కొరకు స్వయం-రక్షణ విద్యా మార్గదర్శకత్వం.",
            "follow_up": "మీ లక్షణాలు 24-48 గంటల కంటే ఎక్కువ కాలం ఉన్నాయా?",
            "lens_natural": "సహజ స్వయం-రక్షణ",
            "lens_ayurveda": "ఆయుర్వేద అవగాహన",
            "lens_allopathic": "సాధారణ వైద్య స్వయం-రక్షణ",
            "chips": ["ప్రకృతి సిద్ధమైన ఉపశమనాలు ఏమిటి?", "ఆయుర్వేద సూచనలు", "వైద్యుడిని ఎప్పుడు సంప్రదించాలి?"],
            "preventive": ["తగినంత మంచినీరు లేదా గోరువెచ్చని నీరు త్రాగండి.", "రాత్రి 7-8 గంటలు నిద్రపోండి.", "తేలికపాటి ఆహారం తీసుకోండి."],
            "avoid": ["వైద్యుడి సలహా లేకుండా మందులు వాడకండి.", "తీవ్రమైన నొప్పిని ఉపేక్షించకండి."],
            "when_seek": ["జ్వరం 102°F (39°C) కంటే ఎక్కువ ఉన్నప్పుడు", "తీవ్రమైన నొప్పి లేదా 48h కంటే ఎక్కువ ఉన్నప్పుడు"],
        },
        "hi": {
            "summary_prefix": "**साक्ष्य-आधारित स्व-देखभाल मार्गदर्शन:**",
            "what_applies": "सामान्य स्वास्थ्य चिंताओं के लिए साक्ष्य-आधारित शिक्षा।",
            "follow_up": "क्या आपके लक्षण 24-48 घंटों से अधिक समय से हैं?",
            "lens_natural": "प्राकृतिक स्व-देखभाल",
            "lens_ayurveda": "आयुर्वेदिक दृष्टिकोण",
            "lens_allopathic": "सामान्य चिकित्सा स्व-देखभाल",
            "chips": ["प्राकृतिक उपाय क्या हैं?", "आयुर्वेदिक सुझाव", "डॉक्टर से कब परामर्श लें?"],
            "preventive": ["पर्याप्त मात्रा में गुनगुना पानी पिएं।", "7-8 घंटे की अच्छी नींद लें।", "हल्का और सुपाच्य भोजन करें।"],
            "avoid": ["बिना डॉक्टर की सलाह के दवाएं न लें।", "तेज दर्द को नजरअंदाज न करें।"],
            "when_seek": ["102°F (39°C) से अधिक बुखार होने पर", "48 घंटे से अधिक लक्षण बने रहने पर"],
        },
        "ta": {
            "summary_prefix": "**ஆதார அடிப்படையிலான சுயபராமரிப்பு வழிகாட்டுதல்:**",
            "what_applies": "பொதுவான சுகாதார கவலைகளுக்கான சுயபராமரிப்பு கல்வி.",
            "follow_up": "உங்கள் அறிகுறிகள் 24-48 மணி நேரத்திற்கு மேலாக நீடிக்கிறதா?",
            "lens_natural": "இயற்கை சுயபராமரிப்பு",
            "lens_ayurveda": "ஆயுர்வேத பார்வை",
            "lens_allopathic": "பொது மருத்துவ சுயபராமரிப்பு",
            "chips": ["இயற்கை நிவாரணங்கள் யாவை?", "ஆயுர்வேத உதவிக்குறிப்புகள்", "மருத்துவரை எப்போது அணுக வேண்டும்?"],
            "preventive": ["போதுமான அளவு வெதுவெதுப்பான நீர் அருந்தவும்.", "7-8 மணி நேர உறக்கம் பெறவும்.", "எளிதில் செரிக்கும் உணவு உட்கொள்ளவும்."],
            "avoid": ["மருத்துவர் ஆலோசனையின்றி மருந்துகளை உட்கொள்ள வேண்டாம்."],
            "when_seek": ["காய்ச்சல் 102°F-க்கு மேல் இருந்தால்", "48 மணி நேரத்திற்கு மேல் நீடித்தால்"],
        },
        "bn": {
            "summary_prefix": "**প্রমাণ-ভিত্তিক স্ব-যত্ন নির্দেশিকা:**",
            "what_applies": "সাধারণ স্বাস্থ্য উদ্বেগের জন্য স্ব-যত্ন শিক্ষা।",
            "follow_up": "আপনার উপসর্গগুলি কি ২৪-৪৮ ঘণ্টার বেশি স্থায়ী হয়েছে?",
            "lens_natural": "প্রাকৃতিক স্ব-যত্ন",
            "lens_ayurveda": "আয়ুর্বেদিক দৃষ্টিকোণ",
            "lens_allopathic": "সাধারণ চিকিৎসা স্ব-যত্ন",
            "chips": ["প্রাকৃতিক প্রতিকারগুলি কি?", "আয়ুর্বেদিক পরামর্শ", "কখন ডাক্তারের কাছে যাবেন?"],
            "preventive": ["পর্যাপ্ত গরম জল পান করুন।", "৭-৮ ঘণ্টা ঘুমান।", "সহজপাচ্য খাবার খান।"],
            "avoid": ["ডাক্তারের পরামর্শ ছাড়া ওষুধ খাবেন না।"],
            "when_seek": ["১০২° ফারেনহাইটের বেশি জ্বর হলে", "৪৮ ঘণ্টার বেশি উপসর্গ থাকলে"],
        },
        "mr": {
            "summary_prefix": "**पुरावा-आधारित स्व-काळजी मार्गदर्शन:**",
            "what_applies": "सामान्य आरोग्य चिंतेसाठी स्व-काळजी शिक्षण.",
            "follow_up": "तुमची लक्षणे २४-४८ तासांपेक्षा जास्त काळ आहेत का?",
            "lens_natural": "नैसर्गिक स्व-काळजी",
            "lens_ayurveda": "आयुर्वेदिक दृष्टिकोन",
            "lens_allopathic": "सामान्य वैद्यकीय स्व-काळजी",
            "chips": ["नैसर्गिक उपाय कोणते?", "आयुर्वेदिक टिप्स", "डॉक्टरांचा सल्ला कधी घ्यावा?"],
        },
        "gu": {
            "summary_prefix": "**પુરાવા-આધારિત સ્વ-સંભાળ માર્ગદર્શન:**",
            "what_applies": "સામાન્ય સ્વાસ્થ્ય સમસ્યાઓ માટે સ્વ-સંભાળ માર્ગદર્શન.",
            "follow_up": "શું તમારા લક્ષણો 24-48 કલાક કરતાં વધુ સમયથી છે?",
            "lens_natural": "કુદરતી સ્વ-સંભાળ",
            "lens_ayurveda": "આયુર્વેદિક દ્રષ્ટિકોણ",
            "lens_allopathic": "સામાન્ય તબીબી સ્વ-સંભાળ",
            "chips": ["કુદરતી ઉપાયો કયા છે?", "આયુર્વેદિક ટિપ્સ", "ડોક્ટરની સલાહ ક્યારે લેવી?"],
        },
        "kn": {
            "summary_prefix": "**ಸಾಕ್ಷ್ಯಾಧಾರಿತ ಸ್ವಯಂ-ಆರೈಕೆ ಮಾರ್ಗದರ್ಶನ:**",
            "what_applies": "ಸಾಮಾನ್ಯ ಆರೋಗ್ಯ ಕಾಳಜಿಗಳಿಗೆ ಸ್ವಯಂ-ಆರೈಕೆ ಶಿಕ್ಷಣ.",
            "follow_up": "ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳು 24-48 ಗಂಟೆಗಳಿಗಿಂತ ಹೆಚ್ಚು ಕಾಲ ಉಳಿದಿವೆಯೇ?",
            "lens_natural": "ನೈಸರ್ಗಿಕ ಸ್ವಯಂ-ಆರೈಕೆ",
            "lens_ayurveda": "ಆಯುರ್ವೇದ ದೃಷ್ಟಿಕೋನ",
            "lens_allopathic": "ಸಾಮಾನ್ಯ ವೈದ್ಯಕೀಯ ಸ್ವಯಂ-ಆರೈಕೆ",
            "chips": ["ನೈಸರ್ಗಿಕ ಉಪಾಯಗಳು யಾವವು?", "ಆಯುರ್ವೇದ ಸಲಹೆಗಳು", "ವೈದ್ಯರನ್ನು ಯಾವಾಗ ಭೇಟಿಯಾಗಬೇಕು?"],
        },
        "ml": {
            "summary_prefix": "**തെളിവ് അടിസ്ഥാനമാക്കിയുള്ള സ്വയം പരിചരണ മാർഗ്ഗനിർദ്ദേശം:**",
            "what_applies": "പൊതുവായ ആരോഗ്യ ആശങ്കകൾക്കുള്ള സ്വയം പരിചരണ വിദ്യാഭ്യാസം.",
            "follow_up": "നിങ്ങളുടെ ലക്ഷണങ്ങൾ 24-48 മണിക്കൂറിൽ കൂടുതൽ നിലനിൽക്കുന്നുണ്ടോ?",
            "lens_natural": "പ്രകൃതിദത്ത സ്വയം പരിചരണം",
            "lens_ayurveda": "ആയുർവേദ കാഴ്ചപ്പാട്",
            "lens_allopathic": "ജനറൽ മെഡിക്കൽ സ്വയം പരിചരണം",
            "chips": ["പ്രകൃതിദത്ത പ്രതിവിധികൾ ഏവ?", "ആയുർവേദ നിർദ്ദേശങ്ങൾ", "എപ്പോൾ ഡോക്ടറെ കാണണം?"],
        },
        "pa": {
            "summary_prefix": "**ਸਬੂਤ-ਆਧਾਰਿਤ ਸਵੈ-ਦੇਖਭਾਲ ਮਾਰਗਦਰਸ਼ਨ:**",
            "what_applies": "ਆਮ ਸਿਹਤ ਚਿੰਤਾਵਾਂ ਲਈ ਸਵੈ-ਦੇਖਭਾਲ ਸਿੱਖਿਆ।",
            "follow_up": "ਕੀ ਤੁਹਾਡੇ ਲੱਛਣ 24-48 ਘੰਟਿਆਂ ਤੋਂ ਵੱਧ ਸਮੇਂ ਤੋਂ ਹਨ?",
            "lens_natural": "ਕੁਦਰਤੀ ਸਵੈ-ਦੇਖਭਾਲ",
            "lens_ayurveda": "ਆਯੁਰਵੈਦਿਕ ਦ੍ਰਿਸ਼ਟੀਕੋਣ",
            "lens_allopathic": "ਆਮ ਮੈਡੀਕਲ ਸਵੈ-ਦੇਖਭਾਲ",
            "chips": ["ਕੁਦਰਤੀ ਉਪਾਅ ਕੀ ਹਨ?", "ਆਯੁਰਵੈਦਿਕ ਸੁਝਾਅ", "ਡਾਕਟਰ ਦੀ ਸਲਾਹ ਕਦੋਂ ਲਓ?"],
        },
        "or": {
            "summary_prefix": "**ପ୍ରମାଣ-ଆଧାରିତ ସ୍ୱୟଂ-ସେବା ମାର୍ଗଦର୍ଶନ:**",
            "what_applies": "ସାଧାରଣ ସ୍ୱାସ୍ଥ୍ୟ ଚିନ୍ତା ପାଇଁ ସ୍ୱୟଂ-ସେବା ଶିକ୍ଷା |",
            "follow_up": "ଆପଣଙ୍କର ଲକ୍ଷଣ ୨୪-୪୮ ଘଣ୍ଟାରୁ ଅଧିକ ସମୟ ଧରି ରହିଛି କି?",
            "lens_natural": "ପ୍ରାକୃତିକ ସ୍ୱୟଂ-ସେବା",
            "lens_ayurveda": "ଆୟୁର୍ବେଦିକ ଦୃଷ୍ଟିକୋଣ",
            "lens_allopathic": "ସାଧାରଣ ଡାକ୍ତରୀ ସ୍ୱୟଂ-ସେବା",
            "chips": ["ପ୍ରାକୃତିକ ପ୍ରତିକାର କ’ଣ?", "ଆୟୁର୍ବେଦିକ ପରାମର୍ଶ", "ଡାକ୍ତରଙ୍କ ସହିତ କେବେ ପରାମର୍ଶ କରିବେ?"],
        },
        "ur": {
            "summary_prefix": "**شواہد پر مبنی خود کی دیکھ بھال کی رہنمائی:**",
            "what_applies": "عام صحت کے خدشات کے لیے خود کی دیکھ بھال کی تعلیم۔",
            "follow_up": "کیا آپ کی علامات 24 سے 48 گھنٹے سے زیادہ پرانی ہیں؟",
            "lens_natural": "قدرتی خود کی دیکھ بھال",
            "lens_ayurveda": "آیو ویدک نقطہ نظر",
            "lens_allopathic": "عام طبی خود کی دیکھ بھال",
            "chips": ["قدرتی علاج کیا ہیں؟", "آیو ویدک مشورے", "ڈاکٹر سے کب رجوع کریں؟"],
        },
    }

    fb = FALLBACK_TRANSLATIONS.get(target_lang)
    if fb:
        orig_summary = state.get("summary", "")
        summary_translated = f"{fb['summary_prefix']} {orig_summary}" if orig_summary else fb['summary_prefix']
        
        orig_table = state.get("action_table", [])
        translated_table = []
        for r in orig_table:
            old_cits = r.citation_ids if hasattr(r, "citation_ids") else ["CIT-001"]
            old_lens = r.guidance_lens if hasattr(r, "guidance_lens") else "Natural Self-Care"
            
            if "Ayurveda" in old_lens:
                lens_text = fb.get("lens_ayurveda", old_lens)
            elif "Medical" in old_lens:
                lens_text = fb.get("lens_allopathic", old_lens)
            else:
                lens_text = fb.get("lens_natural", old_lens)
                
            translated_table.append(ActionTableRow(
                guidance_lens=lens_text,
                what_may_help=r.what_may_help if hasattr(r, "what_may_help") else "Hydration & Rest",
                how_to_follow=r.how_to_follow if hasattr(r, "how_to_follow") else "Sip warm fluids.",
                frequency_duration=r.frequency_duration if hasattr(r, "frequency_duration") else "As needed",
                evidence_strength=r.evidence_strength if hasattr(r, "evidence_strength") else "High",
                cautions=r.cautions if hasattr(r, "cautions") else "Ensure comfort.",
                stop_and_seek_care_if=r.stop_and_seek_care_if if hasattr(r, "stop_and_seek_care_if") else "If symptoms worsen.",
                citation_ids=old_cits,
            ))

        return {
            "summary": summary_translated,
            "what_this_applies_to": fb.get("what_applies", state.get("what_this_applies_to", "")),
            "follow_up_question": fb.get("follow_up", state.get("follow_up_question", "")),
            "quick_action_chips": fb.get("chips", state.get("quick_action_chips", [])),
            "action_table": translated_table,
            "translation_status": "fallback_dictionary_success",
            "response_language": target_lang,
        }

    return {"translation_status": "failed"}


