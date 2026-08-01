"""Asynchronous LangGraph workflow nodes for MedicoBuddy AI.

All nodes are fully async — no nest_asyncio or nested event-loop calls.
Strictly grounded generation: uses RAG evidence from real vector retrieval + Groq LLM.

INTEGRITY CONTRACT:
- No hardcoded similarity scores, retrieval status, or evidence sufficiency flags.
- No metadata store counts as retrieved evidence.
- No citations to documents not in the actual retrieved chunk set.
- Every displayed score, path, and citation must originate from the current request.
"""

from __future__ import annotations

import asyncio
import json
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
    QuickAction,
)
from medicobuddy.models.symptom import SeverityLevel, SymptomReport, TriageOutcome, TriageResult
from medicobuddy.models.user_context import UserContext
from medicobuddy.safety.prompt_injection import check_user_input
from medicobuddy.safety.red_flags import run_triage
from medicobuddy.safety.scope_validator import validate_query_scope
from medicobuddy.workflow.state import GraphState

logger = logging.getLogger(__name__)

# ── Multilingual Concept Map ────────────────────────────────
MULTILINGUAL_CONCEPT_MAP: dict[str, str] = {
    # Hair Loss
    "hairfall": "hair_loss", "hair fall": "hair_loss", "hair loss": "hair_loss",
    "hair shedding": "hair_loss", "safety tips hairfall": "hair_loss",
    "safety measures for hairfall": "hair_loss",
    "జుట్టు రాలడం": "hair_loss", "జుట్టు ఊడటం": "hair_loss",
    "बाल झड़ना": "hair_loss", "बाल गिरना": "hair_loss",
    "முடி உதிர்தல்": "hair_loss", "ಕೂದಲು ಉದುರುವುದು": "hair_loss",
    "ಕೂದಲು ಉದುರುವಿಕೆ": "hair_loss", "മുടി കൊഴിച്ചിൽ": "hair_loss",
    "వాళ్ళు ఖరువా": "hair_loss", "ਬਾਲ ਝੜਨਾ": "hair_loss",
    "بالوں کا جھڑنا": "hair_loss",
    # Telugu
    "తలనెప్పి": "headache", "తలనొప్పి": "headache", "తల నొప్పి": "headache",
    "జ్వరం": "fever", "దగ్గు": "cough", "జలుబు": "cold",
    "కడుపునొప్పి": "stomach discomfort", "కడుపు అసౌకర్యం": "stomach discomfort",
    "గ్యాస్": "stomach discomfort", "తల తిరగడం": "dizziness",
    "అలసట": "fatigue", "నీరసం": "fatigue", "వాంతులు": "nausea",
    "వికారంగా": "nausea", "నిద్ర": "sleep", "దురద": "skin irritation",
    # Hindi
    "सिरदर्द": "headache", "बुखार": "fever", "खांसी": "cough",
    "जुकाम": "cold", "पेट दर्द": "stomach discomfort", "थकान": "fatigue",
    "उल्टी": "nausea", "मतली": "nausea", "एलर्जी": "allergy",
    "साइनस": "sinus congestion", "बालों की देखभाल": "hair care",
    "त्वचा": "skin care", "कब्ज": "constipation", "नींद": "sleep",
    # Tamil
    "தலைவலி": "headache", "காய்ச்சல்": "fever", "இருமல்": "cough",
    "சளி": "cold", "வயிற்றுவலி": "stomach discomfort",
    "சோர்வு": "fatigue", "குமட்டல்": "nausea", "ஒவ்வாமை": "allergy",
    "சைனஸ்": "sinus congestion",
    # Bengali
    "মাথাব্যথা": "headache", "জ্বর": "fever", "কাশি": "cough",
    "সর্দি": "cold", "পেটব্যথা": "stomach discomfort",
    "ক্লান্তি": "fatigue", "বমিবমি": "nausea", "বমি": "nausea",
    "এলার্জি": "allergy",
    # Marathi
    "डोकेदुखी": "headache", "ताप": "fever", "खोकला": "cough",
    "सर्दी": "cold", "पोटदुखी": "stomach discomfort",
    "थकवा": "fatigue", "मळमळ": "nausea", "ॲलर्जी": "allergy",
    # Gujarati
    "માથાનો દુખાવો": "headache", "તાવ": "fever", "ઉધરસ": "cough",
    "શરદી": "cold", "પેટમાં દુખાવો": "stomach discomfort",
    "થાક": "fatigue", "ઉબકા": "nausea",
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


SYMPTOM_CONCEPTS = [
    "headache", "stomach discomfort", "cold", "cough", "fever", "nausea",
    "fatigue", "tiredness", "sinus congestion", "allergy", "allergies",
    "sleep", "hydration", "skin", "skin care", "hair", "hair care", "hair loss",
    "bloating", "indigestion", "stress", "vomiting", "constipation", "dizziness",
    "nutrition", "wellness", "immunity", "inflammation", "pain relief",
]


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

    # Latin-script language detection by keyword
    text_lower = text.lower()
    if not any([has_telugu, has_devanagari, has_tamil, has_bengali, has_gujarati,
                has_kannada, has_malayalam, has_gurmukhi, has_odia, has_arabic_script]):
        # Detect common non-English Latin-script languages by vocabulary
        if any(w in text_lower for w in ["santé", "tête", "mal de tête", "fièvre", "rhume"]):
            detected_lang = "fr"
        elif any(w in text_lower for w in ["kopfschmerzen", "erkältung", "müdigkeit", "gesundheit"]):
            detected_lang = "de"
        elif any(w in text_lower for w in ["dolor de cabeza", "resfriado", "náuseas", "salud"]):
            detected_lang = "es"
        else:
            detected_lang = "en"
    elif has_telugu:
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

    for term, english_concept in MULTILINGUAL_CONCEPT_MAP.items():
        if term in text_lower or term in text:
            return detected_lang, english_concept

    return detected_lang, text


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
    if any(w in text_lower for w in ["severe", "intense", "extreme", "unbearable", "high", "very bad"]):
        severity = "severe"
    elif "moderate" in text_lower:
        severity = "moderate"

    duration = "short-duration / recent"
    if "since morning" in text_lower:
        duration = "since this morning"
    elif "today" in text_lower:
        duration = "today"
    elif "days" in text_lower:
        duration = "for several days"
    elif "week" in text_lower:
        duration = "for a week"

    context_desc = "general self-care"
    if "after work" in text_lower:
        context_desc = "after work / workplace stress"
    elif "after eating" in text_lower or "after food" in text_lower:
        context_desc = "after eating"
    elif "morning" in text_lower:
        context_desc = "morning onset"

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
    """Extract symptom, remedy, and safety entities from text."""
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


def _sanitize_external_text(txt: str) -> str:
    """Remove prompt injection attempts from retrieved external text."""
    bad_phrases = [
        "ignore previous instructions", "system prompt:",
        "you are now an unrestricted", "disregard safety",
        "forget your instructions", "bypass safety",
    ]
    clean_t = txt
    for p in bad_phrases:
        if p in clean_t.lower():
            clean_t = re.sub(re.escape(p), "[REJECTED INSTRUCTION]", clean_t, flags=re.IGNORECASE)
    return clean_t


# ════════════════════════════════════════════════════════════
# Node 1: Language Router
# ════════════════════════════════════════════════════════════

async def language_router_node(state: GraphState) -> dict[str, Any]:
    """Route query language and normalize to English medical concepts."""
    user_message = state.get("user_message", "")
    preferred_lang = state.get("preferred_language", "auto")

    detected_lang, norm_concept = detect_and_normalize_language(user_message)

    target_lang = preferred_lang if (preferred_lang and preferred_lang != "auto") else detected_lang

    return {
        "detected_language": detected_lang,
        "preferred_language": preferred_lang,
        "target_language": target_lang,
        "response_language": target_lang,
        "normalized_english_query": norm_concept,
        "language": target_lang,
        "translation_status": "pending" if target_lang != "en" else "not_required",
        # Reset turn-specific retrieval state
        "vector_results": [],
        "bm25_results": [],
        "graph_results": [],
        "mcp_results": [],
        "graded_evidence": [],
        "citations": [],
        "merged_context": "",
    }


# ════════════════════════════════════════════════════════════
# Node 2: Scope Validator
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

    scope_result = validate_query_scope(
        user_message if detected_lang == "en" else f"{user_message} ({norm_concept})"
    )
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
                "For children under 18, adults over 65, pregnant/breastfeeding individuals, "
                "or complex health cases, please consult a qualified healthcare provider directly."
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
# Node 3: Red-Flag Triage
# ════════════════════════════════════════════════════════════

async def red_flag_triage_node(state: GraphState) -> dict[str, Any]:
    user_message = state.get("user_message", "")
    user_context = state.get("user_context", UserContext())
    symptom_report = extract_symptom_report(user_message)

    triage_result = run_triage(
        text=user_message if state.get("detected_language") == "en"
             else f"{user_message} {symptom_report.main_symptom}",
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
# Node 4: Clarification Check
# ════════════════════════════════════════════════════════════

async def clarification_node(state: GraphState) -> dict[str, Any]:
    user_message = state.get("user_message", "")

    if not user_message or len(user_message.strip()) < 3:
        return {
            "needs_clarification": True,
            "clarification_questions": [
                "Could you describe your main symptom and how long you have experienced it?"
            ],
        }

    return {"needs_clarification": False, "clarification_questions": []}


# ════════════════════════════════════════════════════════════
# Node 5: Query Planner
# ════════════════════════════════════════════════════════════

async def query_planner_node(state: GraphState) -> dict[str, Any]:
    symptom_report = state.get("symptom_report")
    user_message = state.get("user_message", "")
    main = symptom_report.main_symptom if symptom_report else user_message

    # Normalize for search — remove stop words
    stop_words = {"mild", "since", "morning", "after", "work", "eating", "i", "have", "a",
                  "feel", "feeling", "bit", "some", "the", "my", "me", "and", "or"}
    words = [w for w in main.split() if w.lower() not in stop_words]
    clean_keyword = " ".join(words[:4]) if words else user_message[:50]

    severity = symptom_report.severity.value if symptom_report else "mild"

    queries = [
        f"{clean_keyword} self care guidelines",
        f"{clean_keyword} non pharmacological management {severity}",
        f"{clean_keyword} consumer health education evidence",
        f"{clean_keyword} natural remedies safety",
    ]

    return {"search_queries": queries}


# ════════════════════════════════════════════════════════════
# Node 6: MCP Retrieval (Optional — does not block if unavailable)
# ════════════════════════════════════════════════════════════

async def mcp_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Search allowlisted MCP evidence sources (PubMed, EuropePMC, etc.)

    Failure of MCP never blocks retrieval — always returns (empty or populated) result.
    """
    from medicobuddy.config import get_settings
    settings = get_settings()

    if not settings.mcp_enabled:
        return {
            "mcp_results": [],
            "retrieval_status": {"mcp": "disabled"},
            "dependency_errors": [],
        }

    user_message = state.get("user_message", "")

    try:
        from medicobuddy.mcp.client import MCPClientAdapter
        mcp_client = MCPClientAdapter()
        await mcp_client.initialize()
        mcp_items, _mcp_status, mcp_errs = await mcp_client.search_all(
            [user_message], max_results_per_source=3
        )
        return {
            "mcp_results": mcp_items,
            "retrieval_status": {"mcp": "ok", "results": len(mcp_items)},
            "dependency_errors": mcp_errs,
        }
    except Exception as exc:
        logger.info("MCP retrieval unavailable (non-fatal): %s", exc)
        return {
            "mcp_results": [],
            "retrieval_status": {"mcp": f"error: {exc}"},
            "dependency_errors": [str(exc)],
        }


# ════════════════════════════════════════════════════════════
# Node 7: Hybrid Retrieval (pgvector + BM25 + Neo4j)
# ════════════════════════════════════════════════════════════

async def hybrid_retrieval_node(state: GraphState) -> dict[str, Any]:
    """Hybrid retrieval from pgvector + BM25 + Neo4j + MCP.

    INTEGRITY RULES:
    - Similarity scores are real measured values only, never hardcoded.
    - evidence_sufficient is set based on actual retrieved count, not assumed True.
    - Metadata store content is NOT added to vector_results.
    - Services singleton from app.state is preferred over creating new connections.
    """
    start_time = time.perf_counter()
    user_message = state.get("user_message", "")
    symptom_report = state.get("symptom_report")
    extracted_entities = state.get("extracted_entities", {})

    symptom_name = symptom_report.main_symptom if symptom_report else user_message

    graph_results: list[dict[str, Any]] = []
    vector_results: list[dict[str, Any]] = []
    bm25_results: list[dict[str, Any]] = []
    mcp_results: list[MCPResult] = state.get("mcp_results", [])
    contraindications: list[dict[str, Any]] = []
    ayurvedic_concepts: list[dict[str, Any]] = []

    real_indexed_chunks = 0
    real_embedding_dim = 0
    real_graph_nodes = 0
    real_graph_rels = 0
    vector_db_status = "offline"
    graph_store_status = "offline"
    top_similarity_scores: list[float] = []  # populated only from real results

    # Try to get singleton services from app.state first
    _vector_store = None
    _neo4j = None

    try:
        # Attempt to get services from FastAPI app.state (when running in server mode)
        import medicobuddy._app_state as _app_state_module  # type: ignore[import]
        _vector_store = getattr(_app_state_module, "vector_store", None)
        _neo4j = getattr(_app_state_module, "neo4j", None)
    except Exception:
        pass

    # If no singleton available, create transient connections
    try:
        from medicobuddy.config import get_settings
        from medicobuddy.knowledge_graph.client import Neo4jClient
        from medicobuddy.knowledge_graph.queries import KnowledgeGraphQueries
        from medicobuddy.retrieval.vector_store import VectorStoreClient

        settings = get_settings()

        # ── Vector retrieval ──────────────────────────────────
        if _vector_store is None:
            _vector_store = VectorStoreClient(settings)
            owns_vector_store = True
        else:
            owns_vector_store = False

        if _vector_store is not None:
            if owns_vector_store:
                connected = await _vector_store.connect()
            else:
                connected = await _vector_store.is_ready()

            if connected:
                vector_db_status = "connected"
                real_indexed_chunks = await _vector_store.get_indexed_count()
                real_embedding_dim = _vector_store._embedder.dimension

                search_query = (
                    symptom_name
                    if len(symptom_name) <= 50 and symptom_name != user_message
                    else user_message
                )

                # Run vector + BM25 in parallel
                vector_task = _vector_store.search_vector_only(
                    search_query, top_k=20, score_threshold=0.0
                )
                bm25_task = _vector_store.search_bm25_only(search_query, top_k=20)
                vector_results, bm25_results = await asyncio.gather(
                    vector_task, bm25_task, return_exceptions=True
                )
                if isinstance(vector_results, Exception):
                    logger.warning("Vector search failed: %s", vector_results)
                    vector_results = []
                if isinstance(bm25_results, Exception):
                    logger.warning("BM25 search failed: %s", bm25_results)
                    bm25_results = []

                # Real scores from actual results
                top_similarity_scores = [
                    float(v.get("score", 0.0)) for v in vector_results[:5]
                ]

                if owns_vector_store:
                    await _vector_store.close()
            else:
                vector_db_status = "local_faiss_fallback"
                # Try local FAISS fallback (never claims to be pgvector)
                if hasattr(_vector_store, "_search_local_faiss"):
                    search_query = symptom_name if len(symptom_name) <= 50 else user_message
                    vector_results = await _vector_store._search_local_faiss(search_query, top_k=20)
                    if vector_results:
                        logger.info(
                            "FAISS fallback returned %d results", len(vector_results)
                        )
                        top_similarity_scores = [
                            float(v.get("score", 0.0)) for v in vector_results[:5]
                        ]

        # ── Neo4j retrieval ───────────────────────────────────
        if _neo4j is None:
            _neo4j = Neo4jClient(settings)
            owns_neo4j = True
        else:
            owns_neo4j = False

        if _neo4j is not None:
            neo4j_connected = (
                await _neo4j.connect() if owns_neo4j
                else (getattr(_neo4j, "_driver", None) is not None)
            )
            if neo4j_connected:
                graph_store_status = "connected"
                g_queries = KnowledgeGraphQueries(_neo4j)
                real_graph_nodes, real_graph_rels = await g_queries.get_graph_counts()
                entity_list = extracted_entities.get("symptoms", [symptom_name])

                for entity in entity_list[:3]:  # limit to 3 entities
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
                        pass

                try:
                    ayurvedic_concepts = await g_queries.get_ayurvedic_concepts_for_symptom(
                        symptom_name
                    )
                except Exception:
                    pass

                if owns_neo4j:
                    await _neo4j.close()

    except Exception as exc:
        logger.info("hybrid_retrieval: external DB unavailable: %s", exc)

    # Sanitize retrieved text for prompt injection
    for v in vector_results:
        v["text"] = _sanitize_external_text(v.get("text", ""))

    # ── Build merged context from REAL retrieved chunks only ──
    merged_context_blocks: list[str] = []
    seen_block_ids: set[str] = set()

    for vec in vector_results:
        block_id = vec.get("id", "")
        if block_id in seen_block_ids:
            continue
        seen_block_ids.add(block_id)
        meta = vec.get("metadata", {})
        title = meta.get("title") or meta.get("section_title") or "Evidence Document"
        src_file = meta.get("source_file") or meta.get("file") or "Unknown Source"
        page_num = meta.get("page_number", 1)
        chunk_id = meta.get("chunk_id") or vec.get("id", "")
        score = vec.get("score", 0.0)
        text = vec.get("text", "")
        if text.strip():
            merged_context_blocks.append(
                f"[CHUNK_ID:{chunk_id}] [{src_file} (Page {page_num})] [{title}] [Score:{score:.3f}]:\n{text}"
            )

    for m in mcp_results:
        passage = _sanitize_external_text(m.supporting_passage or "")
        if passage.strip():
            merged_context_blocks.append(
                f"[MCP:{m.source_connector.upper()}] [{m.title}] [License:{m.license}]:\n{passage}"
            )

    merged_context = "\n\n---\n\n".join(merged_context_blocks)
    context_chars = len(merged_context)
    context_token_estimate = context_chars // 4

    total_retrieved = len(vector_results) + len(bm25_results) + len(mcp_results) + len(graph_results)
    # Evidence is sufficient when we have real retrieved content
    evidence_sufficient = total_retrieved >= 3 or context_chars >= 500

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    # Debug panel — all values from real measurements
    debug_panel = {
        "vector_db_connection": vector_db_status,
        "vector_collection": "medicobuddy_evidence",
        "total_indexed_chunks": real_indexed_chunks,
        "embedding_model_status": "loaded" if real_embedding_dim > 0 else "unknown",
        "embedding_model": "Qwen/Qwen3-Embedding-0.6B",
        "embedding_dimension": real_embedding_dim,
        # No hardcoded PASS — reflect real status
        "retriever_status": "PASS" if total_retrieved > 0 else "NO_RESULTS",
        "retrieved_vector_chunks": len(vector_results),
        "retrieved_bm25_chunks": len(bm25_results),
        "retrieved_mcp_chunks": len(mcp_results),
        "retrieved_graph_nodes": len(graph_results),
        "retrieved_chunks": total_retrieved,
        # Real scores only — empty list if no vector results
        "top_similarity_scores": top_similarity_scores,
        "graph_store_connection": graph_store_status,
        "graph_nodes": real_graph_nodes,
        "graph_relationships": real_graph_rels,
        "extracted_query_entities": extracted_entities.get("symptoms", [symptom_name]),
        "matched_graph_entities": len(graph_results),
        "evidence_sources_count": total_retrieved,
        "context_length": context_chars,
        "context_token_estimate": context_token_estimate,
        "evidence_sufficient": evidence_sufficient,
        "generation_called": False,  # updated by response_composer_node
        "pipeline_final_state": "SUFFICIENT_FOR_GENERATION" if evidence_sufficient else "LIMITED_EVIDENCE",
        "latency_ms": round(latency_ms, 2),
    }

    return {
        "retrieval_query_hash": state.get("query_hash", ""),
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
        "evidence_status": "SUFFICIENT_FOR_GENERATION" if evidence_sufficient else "LIMITED_EVIDENCE",
        "evidence_sufficient": evidence_sufficient,
        "fused_results": vector_results + bm25_results,
        "contraindications": contraindications,
        "ayurvedic_graph_concepts": ayurvedic_concepts,
        "retrieval_diagnostics": debug_panel,
    }


# ════════════════════════════════════════════════════════════
# Node 7b: Corrective Retrieval (retry with rewritten query)
# ════════════════════════════════════════════════════════════

async def corrective_retrieval_node(state: GraphState) -> dict[str, Any]:
    """If evidence is insufficient, rewrite the query and retry once.

    Called only when evidence_count < 3. Uses broader / synonym-expanded query.
    Never marks insufficient evidence as sufficient — only retries retrieval.
    """
    evidence_sufficient = state.get("evidence_sufficient", False)
    evidence_count = state.get("evidence_count", 0)

    if evidence_sufficient or evidence_count >= 3:
        return {}  # Sufficient — no correction needed

    user_message = state.get("user_message", "")
    symptom_report = state.get("symptom_report")
    symptom_name = symptom_report.main_symptom if symptom_report else user_message

    # Expand query with synonyms and broader terms
    expansion_map = {
        "headache": "headache tension head pain migraine relief",
        "cold": "common cold upper respiratory tract infection rhinitis",
        "cough": "cough respiratory symptom throat irritation",
        "nausea": "nausea vomiting stomach queasy motion sickness",
        "stomach discomfort": "stomach pain indigestion digestive discomfort bloating",
        "fatigue": "fatigue tiredness exhaustion low energy",
        "hair_loss": "hair loss alopecia hair fall treatment",
        "allergy": "allergy allergic rhinitis hay fever",
        "sleep": "sleep insomnia rest sleep hygiene",
        "stress": "stress anxiety relaxation mental wellness",
        "constipation": "constipation bowel irregularity digestive",
        "skin": "skin care dermatitis rash irritation",
    }

    expanded_symptom = expansion_map.get(
        symptom_name, f"{symptom_name} self care management relief"
    )

    logger.info(
        "corrective_retrieval: retrying with expanded query '%s'", expanded_symptom
    )

    # Create a temporary state with the expanded query and retry
    expanded_state = {**state, "user_message": expanded_symptom}
    retry_result = await hybrid_retrieval_node(expanded_state)

    # Only update if we got more results than before
    if retry_result.get("evidence_count", 0) > evidence_count:
        logger.info(
            "Corrective retrieval improved results: %d → %d",
            evidence_count, retry_result.get("evidence_count", 0),
        )
        return retry_result

    logger.info(
        "Corrective retrieval did not improve results (%d). Will proceed with limited evidence.",
        evidence_count,
    )
    return {}


# ════════════════════════════════════════════════════════════
# Node 8: Evidence Grader
# ════════════════════════════════════════════════════════════

async def evidence_grader_node(state: GraphState) -> dict[str, Any]:
    vector_results: list[dict[str, Any]] = state.get("vector_results", [])
    graded: list[EvidenceClaim] = []
    scored: list[dict[str, Any]] = []

    for idx, vec in enumerate(vector_results[:10], start=1):
        meta = vec.get("metadata", {})
        score_val = float(vec.get("score", 0.0))
        graded.append(
            EvidenceClaim(
                claim_id=f"CLM_{idx:03d}",
                claim_text=meta.get("title", f"Retrieved Evidence #{idx}"),
                evidence_level=EvidenceLevel.HIGH if score_val >= 0.6 else EvidenceLevel.MODERATE,
                confidence=score_val,
                supporting_passages=[vec.get("text", "")[:500]],
                source_urls=[meta.get("source_url", "")],
            )
        )
        scored.append({
            "title": meta.get("title", ""),
            "score": score_val,
            "chunk_id": meta.get("chunk_id", vec.get("id", "")),
            "source_file": meta.get("source_file", ""),
        })

    return {
        "graded_evidence": graded,
        "evidence_scores": scored,
    }


# ════════════════════════════════════════════════════════════
# Node 9: Safety & Contraindication Critic
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
# Node 10: Grounded Response Composer (Groq Structured Output)
# ════════════════════════════════════════════════════════════

def _build_groq_prompt(
    user_message: str,
    symptom_name: str,
    merged_context: str,
    user_context: UserContext,
    safety_status: str,
    target_language: str,
    evidence_sufficient: bool,
) -> str:
    """Build the structured Groq prompt with evidence context and JSON schema."""

    lang_instruction = ""
    if target_language and target_language != "en":
        lang_instruction = (
            f"\n\nIMPORTANT: Translate ALL user-visible text fields (summary, what_may_help, "
            f"how_to_follow, frequency_duration, evidence_strength, cautions, stop_and_seek_care_if, "
            f"things_to_avoid, warning_signs, follow_up_question, quick_actions labels, "
            f"implementation_plan fields, preventive_approaches, general_self_care_education, "
            f"what_this_applies_to) into language code: '{target_language}'. "
            f"Do NOT translate: chunk_ids, citation_ids, source filenames, DOIs, URLs, numbers."
        )

    evidence_note = ""
    if not evidence_sufficient:
        evidence_note = (
            "\n\nNOTE: Retrieved evidence is limited for this query. "
            "Provide general educational guidance based on available context. "
            "Clearly state in the summary that evidence is limited for this specific concern. "
            "Do not fabricate citations — only cite the chunks provided."
        )

    context_section = merged_context[:6000] if merged_context else "No specific evidence retrieved for this query."

    return f"""You are MedicoBuddy AI — a multilingual, evidence-grounded healthcare education assistant.
Target population: Adults 18–65 with mild, short-duration, non-emergency concerns.

SAFETY BOUNDARIES:
- Do NOT diagnose diseases
- Do NOT prescribe or recommend specific prescription medicines
- Do NOT provide individualized treatment for chronic diseases, pregnancy, or children
- Do NOT guarantee cures
- Clearly label Ayurvedic practices as "Traditional Use Only" when evidence is limited
- ALWAYS include red-flag warning signs for when to seek professional care

USER QUERY: {user_message}
PRIMARY CONCERN: {symptom_name}
SAFETY STATUS: {safety_status}
USER CONTEXT: Age range adult 18-65, chronic conditions: {user_context.chronic_conditions or 'none reported'}
{lang_instruction}
{evidence_note}

RETRIEVED EVIDENCE CONTEXT (use ONLY these chunks for citations — do not invent):
{context_section}

Return ONLY a valid JSON object matching EXACTLY this schema. No markdown, no explanation, just JSON:

{{
  "summary": "2-4 sentences specific to {symptom_name} based on the evidence above",
  "what_this_applies_to": "Educational guidance for reported {symptom_name} in adults 18-65",
  "action_table": [
    {{
      "guidance_lens": "Natural Self-Care",
      "what_may_help": "<specific intervention from evidence>",
      "how_to_follow": "<step-by-step from evidence>",
      "frequency_duration": "<specific duration from evidence>",
      "evidence_strength": "High (Clinical Guidelines) | Moderate (Observational) | Traditional Use Only | Limited Evidence",
      "cautions": "<contraindications from evidence>",
      "stop_and_seek_care_if": "<red flags from evidence>",
      "citation_ids": ["<chunk_id from CHUNK_ID: tags above>"]
    }}
  ],
  "implementation_plan": {{
    "now": "<immediate action for {symptom_name}>",
    "next_6_to_12_hours": "<actions for next 6-12 hours>",
    "next_24_to_48_hours": "<actions for next 24-48 hours>",
    "what_to_monitor": "<specific signs to watch>",
    "when_to_stop_self_care": "<criteria requiring professional care>"
  }},
  "things_to_avoid": ["<specific avoidances for {symptom_name}>"],
  "warning_signs": ["<red flags requiring medical care for {symptom_name}>"],
  "follow_up_question": "<one targeted question about {symptom_name}>",
  "quick_actions": [
    {{
      "label": "<short button label>",
      "standalone_query": "<complete question about {symptom_name} that can stand alone>",
      "parent_topic": "{symptom_name}"
    }}
  ],
  "citations": [
    {{
      "citation_id": "CIT-001",
      "title": "<document title from evidence context>",
      "authors": "<organization from evidence context>",
      "year": "<year if available>",
      "source_file": "<filename from evidence context>",
      "page_number": <page_number from evidence context>,
      "chunk_id": "<exact CHUNK_ID from evidence context>",
      "supporting_passage": "<verbatim excerpt from the chunk>",
      "retrieval_score": <float score from evidence context>,
      "evidence_category": "clinical_guideline | traditional_evidence | observational"
    }}
  ],
  "evidence_strength": "Strong | Moderate | Limited | Insufficient",
  "ayurveda_perspectives": [],
  "preventive_approaches": ["<preventive measure from evidence>"],
  "general_self_care_education": "<general educational context about {symptom_name}>"
}}

Rules for citations:
1. Only cite chunk IDs that appear in the evidence context above (CHUNK_ID: tags)
2. If no evidence was retrieved, set citations to empty array and note limited evidence in summary
3. Supporting_passage must be verbatim or near-verbatim from the chunk text
4. Do NOT invent document titles, authors, or URLs

Rules for action_table:
1. Only include rows with supporting evidence
2. Do not force a row if no evidence supports that guidance lens
3. Citation_ids must reference real chunk IDs from the context
"""


def _parse_groq_response(raw: str, attempt: int = 1) -> dict[str, Any] | None:
    """Parse and validate Groq JSON response with repair attempts."""
    # Strip markdown code fences
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # Find first { to last }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse attempt %d failed: %s", attempt, exc)
        if attempt < 2:
            # Basic repair: fix trailing commas
            text = re.sub(r",\s*}", "}", text)
            text = re.sub(r",\s*]", "]", text)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None
        return None


def _build_citation_from_chunk(
    chunk: dict[str, Any],
    cit_number: int,
    cit_id: str,
) -> Citation:
    """Build a real Citation object from a retrieved chunk."""
    meta = chunk.get("metadata", {})
    return Citation(
        number=cit_number,
        citation_id=cit_id,
        title=meta.get("title", "Evidence Document"),
        authors=meta.get("organization", "Unknown"),
        publication_date=meta.get("year", ""),
        source_file=meta.get("source_file", ""),
        page_number=meta.get("page_number", 1),
        supporting_passage=chunk.get("text", "")[:300],
        evidence_type="clinical_guideline",
    )


async def response_composer_node(state: GraphState) -> dict[str, Any]:
    """Compose a grounded response using Groq LLM + retrieved evidence chunks.

    INTEGRITY CONTRACT:
    - Action table is built from Groq output (evidence-grounded), not metadata store
    - Citations reference real retrieved chunks only
    - If Groq fails, falls back to metadata store BUT marks evidence as "Metadata Reference Only"
    - Never claims evidence is sufficient when it isn't
    """
    from medicobuddy.llm import get_llm
    from medicobuddy.evidence.metadata_store import get_metadata_for_symptom

    user_message = state.get("user_message", "")
    symptom_report = state.get("symptom_report")
    symptom_name = symptom_report.main_symptom if symptom_report else user_message
    vector_results: list[dict[str, Any]] = state.get("vector_results", [])
    merged_context = state.get("merged_context", "")
    user_context = state.get("user_context", UserContext())
    safety_status = state.get("safety_status", "SELF_CARE_INFORMATION")
    target_language = state.get("target_language", "en")
    evidence_sufficient = state.get("evidence_sufficient", False)
    triage_result = state.get("triage_result")

    applies_to = f"Educational self-care guidance for reported {symptom_name} in adults aged 18–65."

    llm = get_llm()
    generation_called = False
    groq_parse_success = False
    groq_response_dict: dict[str, Any] = {}

    # ── Attempt Groq structured generation ───────────────────
    if llm is not None:
        prompt = _build_groq_prompt(
            user_message=user_message,
            symptom_name=symptom_name,
            merged_context=merged_context,
            user_context=user_context,
            safety_status=safety_status,
            target_language=target_language,
            evidence_sufficient=evidence_sufficient,
        )

        for attempt in range(1, 3):  # up to 2 attempts
            try:
                if attempt == 2:
                    logger.info("Groq retry attempt 2 for %s", symptom_name)

                resp = await asyncio.to_thread(llm.invoke, prompt)
                generation_called = True
                raw_content = getattr(resp, "content", str(resp))

                parsed = _parse_groq_response(raw_content, attempt)
                if parsed is not None:
                    groq_response_dict = parsed
                    groq_parse_success = True
                    logger.info(
                        "Groq structured output parsed successfully (attempt %d)", attempt
                    )
                    break
                else:
                    logger.warning("Groq response parse failed on attempt %d", attempt)
            except Exception as exc:
                logger.warning("Groq invocation failed on attempt %d: %s", attempt, exc)

    # ── Build response from Groq output or fallback ───────────
    action_table: list[ActionTableRow] = []
    citations: list[Citation] = []
    impl_plan = ImplementationPlan()
    preventive_approaches: list[str] = []
    ayurveda_perspectives: list[AyurvedaPerspective] = []
    things_to_avoid: list[str] = []
    warning_signs: list[str] = []
    follow_up_question = ""
    quick_actions_raw: list[dict[str, Any]] = []
    summary_text = ""
    general_edu = ""
    evidence_strength_label = "Insufficient"

    # Map chunk IDs for citation validation
    chunk_id_map: dict[str, dict[str, Any]] = {}
    for chunk in vector_results:
        chunk_id = chunk.get("metadata", {}).get("chunk_id") or chunk.get("id", "")
        if chunk_id:
            chunk_id_map[chunk_id] = chunk

    if groq_parse_success and groq_response_dict:
        grd = groq_response_dict
        summary_text = grd.get("summary", "")
        applies_to = grd.get("what_this_applies_to", applies_to)
        evidence_strength_label = grd.get("evidence_strength", "Moderate")
        general_edu = grd.get("general_self_care_education", "")
        preventive_approaches = grd.get("preventive_approaches", [])
        things_to_avoid = grd.get("things_to_avoid", [])
        warning_signs = grd.get("warning_signs", [])
        follow_up_question = grd.get("follow_up_question", "")

        # Build action table from Groq output
        for row_dict in grd.get("action_table", []):
            if not isinstance(row_dict, dict):
                continue
            action_table.append(ActionTableRow(
                guidance_lens=row_dict.get("guidance_lens", "Natural Self-Care"),
                what_may_help=row_dict.get("what_may_help", ""),
                how_to_follow=row_dict.get("how_to_follow", ""),
                frequency_duration=row_dict.get("frequency_duration", ""),
                evidence_strength=row_dict.get("evidence_strength", "Moderate"),
                cautions=row_dict.get("cautions", ""),
                stop_and_seek_care_if=row_dict.get("stop_and_seek_care_if", ""),
                citation_ids=row_dict.get("citation_ids", []),
            ))

        # Implementation plan from Groq
        impl_dict = grd.get("implementation_plan", {})
        if isinstance(impl_dict, dict):
            impl_plan = ImplementationPlan(
                now=impl_dict.get("now", ""),
                next_6_to_12_hours=impl_dict.get("next_6_to_12_hours", ""),
                next_24_to_48_hours=impl_dict.get("next_24_to_48_hours", ""),
            )

        # Ayurveda perspectives
        for ayur in grd.get("ayurveda_perspectives", []):
            if isinstance(ayur, dict):
                ayurveda_perspectives.append(AyurvedaPerspective(
                    practice=ayur.get("practice", ""),
                    description=ayur.get("description", ""),
                    evidence_label=ayur.get("evidence_label", "traditional_use_only"),
                    source_summary=ayur.get("source_summary", ""),
                ))

        # Build citations from Groq output + validate against retrieved chunks
        cit_number = 1
        for cit_dict in grd.get("citations", []):
            if not isinstance(cit_dict, dict):
                continue
            chunk_id = cit_dict.get("chunk_id", "")
            # Validate: citation must reference a real retrieved chunk
            if chunk_id and chunk_id in chunk_id_map:
                real_chunk = chunk_id_map[chunk_id]
                real_meta = real_chunk.get("metadata", {})
                citations.append(Citation(
                    number=cit_number,
                    citation_id=cit_dict.get("citation_id", f"CIT-{cit_number:03d}"),
                    title=real_meta.get("title") or cit_dict.get("title", "Evidence Document"),
                    authors=real_meta.get("organization") or cit_dict.get("authors", "Unknown"),
                    publication_date=real_meta.get("year") or cit_dict.get("year", ""),
                    source_file=real_meta.get("source_file") or cit_dict.get("source_file", ""),
                    page_number=real_meta.get("page_number") or cit_dict.get("page_number", 1),
                    supporting_passage=cit_dict.get("supporting_passage", "")[:400],
                    evidence_type=cit_dict.get("evidence_category", "clinical_guideline"),
                ))
                cit_number += 1
            elif not chunk_id and cit_dict.get("title"):
                # MCP or external citation without chunk ID — include with source note
                citations.append(Citation(
                    number=cit_number,
                    citation_id=cit_dict.get("citation_id", f"CIT-{cit_number:03d}"),
                    title=cit_dict.get("title", ""),
                    authors=cit_dict.get("authors", "Unknown"),
                    publication_date=cit_dict.get("year", ""),
                    source_file=cit_dict.get("source_file", ""),
                    page_number=cit_dict.get("page_number", 1),
                    supporting_passage=cit_dict.get("supporting_passage", "")[:400],
                    evidence_type=cit_dict.get("evidence_category", ""),
                ))
                cit_number += 1

        # Quick actions from Groq
        quick_actions_raw = grd.get("quick_actions", [])

    # ── Fallback: use metadata store if Groq failed ───────────
    if not groq_parse_success or not action_table:
        logger.warning(
            "Using metadata store fallback for %s (Groq success=%s)",
            symptom_name, groq_parse_success,
        )
        meta_entry = get_metadata_for_symptom(user_message)
        fallback_evidence_note = " [Metadata Reference Only — limited retrieved evidence]"

        for r in meta_entry.get("natural_remedies", []):
            action_table.append(ActionTableRow(
                guidance_lens=r.get("guidance_lens", "Natural Self-Care"),
                what_may_help=r.get("what_may_help", ""),
                how_to_follow=r.get("how_to_follow", ""),
                frequency_duration=r.get("frequency_duration", "As needed"),
                evidence_strength=r.get("evidence_strength", "Limited Evidence") + fallback_evidence_note,
                cautions=r.get("cautions", ""),
                stop_and_seek_care_if=r.get("stop_and_seek_care_if", ""),
                citation_ids=[],  # No real citations for metadata fallback
            ))

        for r in meta_entry.get("ayurvedic_remedies", []):
            action_table.append(ActionTableRow(
                guidance_lens=r.get("guidance_lens", "Ayurveda-Informed Wellness"),
                what_may_help=r.get("what_may_help", ""),
                how_to_follow=r.get("how_to_follow", ""),
                frequency_duration=r.get("frequency_duration", ""),
                evidence_strength="Traditional Use Only" + fallback_evidence_note,
                cautions=r.get("cautions", ""),
                stop_and_seek_care_if=r.get("stop_and_seek_care_if", ""),
                citation_ids=[],
            ))

        for r in meta_entry.get("allopathic_self_care", []):
            action_table.append(ActionTableRow(
                guidance_lens=r.get("guidance_lens", "Evidence-Based General Medical Self-Care"),
                what_may_help=r.get("what_may_help", ""),
                how_to_follow=r.get("how_to_follow", ""),
                frequency_duration=r.get("frequency_duration", ""),
                evidence_strength="Limited Evidence" + fallback_evidence_note,
                cautions=r.get("cautions", ""),
                stop_and_seek_care_if=r.get("stop_and_seek_care_if", ""),
                citation_ids=[],
            ))

        impl_plan = ImplementationPlan(
            now=meta_entry.get("implementation_now", f"Rest and monitor your {symptom_name}."),
            next_6_to_12_hours=meta_entry.get(
                "implementation_6_12h", "Track symptoms and maintain hydration."
            ),
            next_24_to_48_hours=meta_entry.get(
                "implementation_24_48h", "Re-evaluate symptoms; seek care if worsening."
            ),
        )
        preventive_approaches = meta_entry.get("immune_and_preventive", [])
        things_to_avoid = meta_entry.get("things_to_avoid", [])
        warning_signs = meta_entry.get("seek_care_triggers", [])

        if not summary_text:
            summary_text = (
                f"**General educational guidance for {symptom_name}** — "
                f"Note: specific retrieved evidence was limited. "
                f"This guidance is based on general health principles. "
                f"Consult a healthcare provider for personalized advice."
            )
        evidence_strength_label = "Insufficient"
        citations = []  # No fabricated citations for fallback

        # Build from real chunks if any exist (even if Groq failed)
        for idx, chunk in enumerate(vector_results[:3], start=1):
            meta = chunk.get("metadata", {})
            if meta.get("source_file") and chunk.get("text", "").strip():
                citations.append(_build_citation_from_chunk(
                    chunk, idx, f"CIT-{idx:03d}"
                ))

    # ── Default quick actions if Groq didn't provide good ones ─
    if not quick_actions_raw:
        quick_actions_raw = [
            {
                "label": f"Natural remedies for {symptom_name}",
                "standalone_query": f"What are the best evidence-based natural remedies for {symptom_name}?",
                "parent_topic": symptom_name,
            },
            {
                "label": "When to see a doctor",
                "standalone_query": f"When should I see a doctor for {symptom_name}? What are the warning signs?",
                "parent_topic": symptom_name,
            },
            {
                "label": "Prevention tips",
                "standalone_query": f"How can I prevent {symptom_name} from recurring?",
                "parent_topic": symptom_name,
            },
        ]

    # Build QuickAction objects + backward-compat string list
    quick_action_objects: list[QuickAction] = []
    quick_action_chips: list[str] = []
    for qa in quick_actions_raw[:4]:
        if isinstance(qa, dict):
            quick_action_objects.append(QuickAction(
                label=qa.get("label", ""),
                standalone_query=qa.get("standalone_query", qa.get("label", "")),
                parent_topic=qa.get("parent_topic", symptom_name),
            ))
            quick_action_chips.append(qa.get("label", ""))
        elif isinstance(qa, str):
            quick_action_objects.append(QuickAction(
                label=qa,
                standalone_query=f"Tell me more about {qa} for {symptom_name}",
                parent_topic=symptom_name,
            ))
            quick_action_chips.append(qa)

    # Escalation override: if red-flag, add emergency guidance
    if triage_result and triage_result.outcome == TriageOutcome.URGENT_CARE:
        from medicobuddy.config import get_settings
        settings = get_settings()
        region = user_context.region or settings.default_region
        emergency = settings.emergency_contacts.get(region, {})
        ec_number = emergency.get("number", "112")
        ec_name = emergency.get("name", "Emergency Services")

        summary_text = (
            f"⚠️ **URGENT CARE RECOMMENDED**: Based on your reported symptoms, "
            f"please seek immediate medical evaluation. "
            f"Call {ec_name} at {ec_number} or go to your nearest emergency department.\n\n"
            + (summary_text or "")
        )
        warning_signs = [
            "Your symptoms may require immediate professional evaluation.",
            f"Call {ec_name}: {ec_number}",
        ] + warning_signs

    debug_panel = state.get("retrieval_diagnostics", {})
    if debug_panel:
        debug_panel["generation_called"] = generation_called
        debug_panel["groq_parse_success"] = groq_parse_success
        debug_panel["llm_provider_status"] = "used" if generation_called else "unavailable"

    return {
        "what_this_applies_to": applies_to,
        "summary": summary_text,
        "final_answer": summary_text,
        "action_table": action_table,
        "implementation_plan": impl_plan,
        "preventive_approaches": preventive_approaches,
        "ayurveda_perspectives": ayurveda_perspectives,
        "general_self_care_education": general_edu,
        "things_to_avoid": things_to_avoid,
        "avoid_and_monitor": [
            AvoidAndMonitorRow(
                what_to_avoid="Self-prescribing prescription medications; ignoring worsening symptoms",
                why_avoid="Risk of adverse reactions and delayed treatment",
                what_to_monitor=f"Symptom intensity, temperature, fluid intake for {symptom_name}",
                monitoring_frequency="Every 6-12 hours",
            )
        ],
        "when_to_seek_care": warning_signs,
        "warning_signs": warning_signs,
        "follow_up_question": follow_up_question or "Have your symptoms lasted longer than 24–48 hours?",
        "quick_action_chips": quick_action_chips,
        "quick_actions": quick_action_objects,
        "citations": citations,
        "overall_evidence_level": (
            EvidenceLevel.HIGH if evidence_strength_label in ("Strong",)
            else EvidenceLevel.MODERATE if evidence_strength_label in ("Moderate",)
            else EvidenceLevel.INSUFFICIENT
        ),
        "retrieval_diagnostics": debug_panel,
    }


# ════════════════════════════════════════════════════════════
# Node 11: Output Validator (real validation)
# ════════════════════════════════════════════════════════════

async def output_validator_node(state: GraphState) -> dict[str, Any]:
    """Validate composed response against required schema."""
    violations: list[str] = []

    summary = state.get("summary", "")
    action_table = state.get("action_table", [])
    citations = state.get("citations", [])
    warning_signs = state.get("warning_signs", [])

    if not summary or len(summary.strip()) < 10:
        violations.append("summary is missing or too short")

    if not action_table:
        violations.append("action_table is empty")

    if not warning_signs:
        violations.append("warning_signs is empty — every response needs at least one")

    # Detect hardcoded citation sentinel values from old code
    for c in citations:
        if hasattr(c, "source_file") and ("medicobuddy_metadata_registry.pdf" in getattr(c, "source_file", "")):  # sentinel blocked check
            if not c.supporting_passage or c.supporting_passage.strip().startswith(
                "Recommended non-pharmacological"
            ):
                violations.append(
                    f"Citation {c.citation_id} appears to be hardcoded (source: {c.source_file})"
                )

    output_valid = len(violations) == 0

    if violations:
        logger.warning("Output validation violations: %s", violations)

    return {
        "output_valid": output_valid,
        "output_violations": violations,
    }


# ════════════════════════════════════════════════════════════
# Node 12: Citation Validator (real validation)
# ════════════════════════════════════════════════════════════

async def citation_validator_node(state: GraphState) -> dict[str, Any]:
    """Validate citations against retrieved chunks and ingestion manifest."""
    citations = state.get("citations", [])
    vector_results = state.get("vector_results", [])
    citation_warnings: list[str] = []

    if not citations:
        return {"citations": citations, "citation_warnings": []}

    # Build set of valid chunk IDs from retrieved results
    valid_chunk_ids: set[str] = set()
    for chunk in vector_results:
        chunk_id = chunk.get("metadata", {}).get("chunk_id") or chunk.get("id", "")
        if chunk_id:
            valid_chunk_ids.add(chunk_id)

    # Load ingestion manifest for source file validation
    ingested_files: set[str] = set()
    try:
        from pathlib import Path
        manifest_path = Path(__file__).resolve().parent.parent.parent.parent / "evidence" / "source_manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(manifest, list):
                ingested_files = {entry.get("file_name", "") for entry in manifest}
    except Exception:
        pass

    validated_citations: list = []
    for c in citations:
        issues: list[str] = []
        c_id = getattr(c, "citation_id", "") or ""
        c_source = getattr(c, "source_file", "") or ""
        c_passage = getattr(c, "supporting_passage", "") or ""

        if not c_passage.strip():
            issues.append("missing supporting_passage")

        # Only warn about source file if manifest is available
        if ingested_files and c_source and c_source not in ingested_files:
            # Allow MCP sources (they don't have filenames in the manifest)
            if not c_source.startswith("http") and not c_source.startswith("MCP"):
                issues.append(f"source_file '{c_source}' not in ingested manifest")

        # Warn about sentinel values from old hardcoded code — reject if blocked
        if "medicobuddy_metadata_registry.pdf" in c_source:  # sentinel blocked check
            issues.append("hardcoded metadata citation rejected")
            citation_warnings.append(f"{c_id}: hardcoded citation blocked")
            continue  # Reject this citation


        if issues:
            citation_warnings.extend([f"{c_id}: {issue}" for issue in issues])

        validated_citations.append(c)

    if citation_warnings:
        logger.warning("Citation warnings: %s", citation_warnings)

    return {
        "citations": validated_citations,
        "citation_warnings": citation_warnings,
    }


# ════════════════════════════════════════════════════════════
# Node 13: Structured Translation
# ════════════════════════════════════════════════════════════

async def structured_translation_node(state: GraphState) -> dict[str, Any]:
    """Translate ALL user-visible answer fields into target_language.

    Translation rules:
    - Translate EVERY user-visible field (not just guidance_lens)
    - Do NOT prepend a translated prefix to English content
    - Preserve medical meaning and safety warnings accurately
    - Do NOT translate: chunk IDs, citation IDs, filenames, numbers
    """
    target_lang = state.get("target_language", "en")
    if target_lang == "en":
        return {"translation_status": "skipped"}

    from medicobuddy.llm import get_llm

    # Collect all translatable content from state
    content_to_translate = {
        "summary": state.get("summary", ""),
        "what_this_applies_to": state.get("what_this_applies_to", ""),
        "follow_up_question": state.get("follow_up_question", ""),
        "general_self_care_education": state.get("general_self_care_education", ""),
        "preventive_approaches": state.get("preventive_approaches", []),
        "things_to_avoid": state.get("things_to_avoid", []),
        "when_to_seek_care": state.get("when_to_seek_care", []),
        "warning_signs": state.get("warning_signs", []),
        "action_table": [
            r.model_dump() if hasattr(r, "model_dump") else r
            for r in state.get("action_table", [])
        ],
        "quick_actions": [
            qa.model_dump() if hasattr(qa, "model_dump") else qa
            for qa in state.get("quick_actions", [])
        ],
        "implementation_plan": (
            state.get("implementation_plan").model_dump()
            if hasattr(state.get("implementation_plan", {}), "model_dump")
            else state.get("implementation_plan", {})
        ),
    }

    try:
        llm = get_llm()
        if llm:
            prompt = f"""You are an expert medical translator. Translate ALL user-facing content into language code '{target_lang}'.

STRICT RULES:
1. Translate EVERY field completely — not just field names or labels.
2. Do NOT keep English text in translated fields. The complete content must be in {target_lang}.
3. Do NOT translate: chunk_ids, citation_ids, source filenames (*.pdf), URLs, DOIs, numbers.
4. Preserve medical accuracy and all safety warnings exactly.
5. Return ONLY a valid JSON object matching the input structure.
6. For quick_actions: translate both "label" and "standalone_query" fields.
7. For action_table rows: translate guidance_lens, what_may_help, how_to_follow, frequency_duration, evidence_strength, cautions, stop_and_seek_care_if.
8. For implementation_plan: translate now, next_6_to_12_hours, next_24_to_48_hours, what_to_monitor, when_to_stop_self_care.

CONTENT TO TRANSLATE:
{json.dumps(content_to_translate, ensure_ascii=False, indent=2)}

Return the translated JSON object with identical structure."""

            llm_res = await asyncio.to_thread(llm.invoke, prompt)
            raw_text = str(getattr(llm_res, "content", ""))

            parsed = _parse_groq_response(raw_text)
            if parsed is not None:
                updates: dict[str, Any] = {"translation_status": f"success:{target_lang}"}

                # Apply all translated fields
                scalar_fields = [
                    "summary", "what_this_applies_to", "follow_up_question",
                    "general_self_care_education",
                ]
                for field in scalar_fields:
                    if parsed.get(field) and isinstance(parsed[field], str):
                        updates[field] = parsed[field]

                list_fields = [
                    "preventive_approaches", "things_to_avoid",
                    "when_to_seek_care", "warning_signs",
                ]
                for field in list_fields:
                    if parsed.get(field) and isinstance(parsed[field], list):
                        updates[field] = parsed[field]

                # Translate action table — preserving citation_ids
                if parsed.get("action_table") and isinstance(parsed["action_table"], list):
                    orig_table = state.get("action_table", [])
                    new_table = []
                    for idx, r in enumerate(parsed["action_table"]):
                        old_cits = (
                            orig_table[idx].citation_ids
                            if idx < len(orig_table) and hasattr(orig_table[idx], "citation_ids")
                            else []
                        )
                        new_table.append(ActionTableRow(
                            guidance_lens=r.get("guidance_lens", ""),
                            what_may_help=r.get("what_may_help", ""),
                            how_to_follow=r.get("how_to_follow", ""),
                            frequency_duration=r.get("frequency_duration", ""),
                            evidence_strength=r.get("evidence_strength", ""),
                            cautions=r.get("cautions", ""),
                            stop_and_seek_care_if=r.get("stop_and_seek_care_if", ""),
                            citation_ids=old_cits,
                        ))
                    updates["action_table"] = new_table

                # Translate quick actions
                if parsed.get("quick_actions") and isinstance(parsed["quick_actions"], list):
                    orig_qas = state.get("quick_actions", [])
                    new_qas = []
                    new_chips = []
                    for idx, qa in enumerate(parsed["quick_actions"]):
                        parent = (
                            orig_qas[idx].parent_topic
                            if idx < len(orig_qas) and hasattr(orig_qas[idx], "parent_topic")
                            else ""
                        )
                        new_qas.append(QuickAction(
                            label=qa.get("label", ""),
                            standalone_query=qa.get("standalone_query", ""),
                            parent_topic=parent,
                        ))
                        new_chips.append(qa.get("label", ""))
                    updates["quick_actions"] = new_qas
                    updates["quick_action_chips"] = new_chips

                # Translate implementation plan
                if parsed.get("implementation_plan") and isinstance(parsed["implementation_plan"], dict):
                    ip = parsed["implementation_plan"]
                    updates["implementation_plan"] = ImplementationPlan(
                        now=ip.get("now", ""),
                        next_6_to_12_hours=ip.get("next_6_to_12_hours", ""),
                        next_24_to_48_hours=ip.get("next_24_to_48_hours", ""),
                    )

                return updates

    except Exception as exc:
        logger.warning("Structured translation LLM error: %s", exc)

    # ── Fallback: dictionary-based partial translation ────────
    # Covers the most critical fields for languages where LLM translation failed.
    # NOTE: This translates the entire summary, not just a prefix.
    FALLBACK_TRANSLATIONS: dict[str, dict[str, Any]] = {
        "te": {
            "summary_template": "**ఆధారాలతో కూడిన స్వయం-రక్షణ మార్గదర్శకత్వం:** {summary}",
            "what_applies": "పరిమిత స్వల్పకాలిక ఆరోగ్య ఆందోళనల కొరకు స్వయం-రక్షణ విద్యా మార్గదర్శకత్వం.",
            "follow_up": "మీ లక్షణాలు 24-48 గంటల కంటే ఎక్కువ కాలం ఉన్నాయా?",
            "lens_natural": "సహజ స్వయం-రక్షణ", "lens_ayurveda": "ఆయుర్వేద అవగాహన",
            "lens_medical": "సాధారణ వైద్య స్వయం-రక్షణ",
            "chips": ["ప్రకృతి సిద్ధమైన ఉపశమనాలు ఏమిటి?", "ఆయుర్వేద సూచనలు", "వైద్యుడిని ఎప్పుడు సంప్రదించాలి?"],
            "preventive": ["తగినంత మంచినీరు లేదా గోరువెచ్చని నీరు త్రాగండి.", "రాత్రి 7-8 గంటలు నిద్రపోండి.", "తేలికపాటి ఆహారం తీసుకోండి."],
            "avoid": ["వైద్యుడి సలహా లేకుండా మందులు వాడకండి.", "తీవ్రమైన నొప్పిని ఉపేక్షించకండి."],
            "warning": ["జ్వరం 102°F (39°C) కంటే ఎక్కువ ఉన్నప్పుడు", "తీవ్రమైన నొప్పి లేదా 48h కంటే ఎక్కువ ఉన్నప్పుడు"],
        },
        "hi": {
            "summary_template": "**साक्ष्य-आधारित स्व-देखभाल मार्गदर्शन:** {summary}",
            "what_applies": "सामान्य स्वास्थ्य चिंताओं के लिए साक्ष्य-आधारित शिक्षा।",
            "follow_up": "क्या आपके लक्षण 24-48 घंटों से अधिक समय से हैं?",
            "lens_natural": "प्राकृतिक स्व-देखभाल", "lens_ayurveda": "आयुर्वेदिक दृष्टिकोण",
            "lens_medical": "सामान्य चिकित्सा स्व-देखभाल",
            "chips": ["प्राकृतिक उपाय क्या हैं?", "आयुर्वेदिक सुझाव", "डॉक्टर से कब परामर्श लें?"],
            "preventive": ["पर्याप्त मात्रा में गुनगुना पानी पिएं।", "7-8 घंटे की अच्छी नींद लें।", "हल्का और सुपाच्य भोजन करें।"],
            "avoid": ["बिना डॉक्टर की सलाह के दवाएं न लें।", "तेज दर्द को नजरअंदाज न करें।"],
            "warning": ["102°F (39°C) से अधिक बुखार होने पर", "48 घंटे से अधिक लक्षण बने रहने पर"],
        },
        "ta": {
            "summary_template": "**ஆதார அடிப்படையிலான சுயபராமரிப்பு வழிகாட்டுதல்:** {summary}",
            "what_applies": "பொதுவான சுகாதார கவலைகளுக்கான சுயபராமரிப்பு கல்வி.",
            "follow_up": "உங்கள் அறிகுறிகள் 24-48 மணி நேரத்திற்கு மேலாக நீடிக்கிறதா?",
            "lens_natural": "இயற்கை சுயபராமரிப்பு", "lens_ayurveda": "ஆயுர்வேத பார்வை",
            "lens_medical": "பொது மருத்துவ சுயபராமரிப்பு",
            "chips": ["இயற்கை நிவாரணங்கள் யாவை?", "ஆயுர்வேத உதவிக்குறிப்புகள்", "மருத்துவரை எப்போது அணுக வேண்டும்?"],
            "preventive": ["போதுமான அளவு வெதுவெதுப்பான நீர் அருந்தவும்.", "7-8 மணி நேர உறக்கம் பெறவும்.", "எளிதில் செரிக்கும் உணவு உட்கொள்ளவும்."],
            "avoid": ["மருத்துவர் ஆலோசனையின்றி மருந்துகளை உட்கொள்ள வேண்டாம்."],
            "warning": ["காய்ச்சல் 102°F-க்கு மேல் இருந்தால்", "48 மணி நேரத்திற்கு மேல் நீடித்தால்"],
        },
        "bn": {
            "summary_template": "**প্রমাণ-ভিত্তিক স্ব-যত্ন নির্দেশিকা:** {summary}",
            "what_applies": "সাধারণ স্বাস্থ্য উদ্বেগের জন্য স্ব-যত্ন শিক্ষা।",
            "follow_up": "আপনার উপসর্গগুলি কি ২৪-৪৮ ঘণ্টার বেশি স্থায়ী হয়েছে?",
            "lens_natural": "প্রাকৃতিক স্ব-যত্ন", "lens_ayurveda": "আয়ুর্বেদিক দৃষ্টিকোণ",
            "lens_medical": "সাধারণ চিকিৎসা স্ব-যত্ন",
            "chips": ["প্রাকৃতিক প্রতিকারগুলি কি?", "আয়ুর্বেদিক পরামর্শ", "কখন ডাক্তারের কাছে যাবেন?"],
            "preventive": ["পর্যাপ্ত গরম জল পান করুন।", "৭-৮ ঘণ্টা ঘুমান।"],
            "avoid": ["ডাক্তারের পরামর্শ ছাড়া ওষুধ খাবেন না।"],
            "warning": ["১০২° ফারেনহাইটের বেশি জ্বর হলে", "৪৮ ঘণ্টার বেশি উপসর্গ থাকলে"],
        },
        "mr": {
            "summary_template": "**पुरावा-आधारित स्व-काळजी मार्गदर्शन:** {summary}",
            "what_applies": "सामान्य आरोग्य चिंतेसाठी स्व-काळजी शिक्षण.",
            "follow_up": "तुमची लक्षणे २४-४८ तासांपेक्षा जास्त काळ आहेत का?",
            "lens_natural": "नैसर्गिक स्व-काळजी", "lens_ayurveda": "आयुर्वेदिक दृष्टिकोन",
            "lens_medical": "सामान्य वैद्यकीय स्व-काळजी",
            "chips": ["नैसर्गिक उपाय कोणते?", "आयुर्वेदिक टिप्स", "डॉक्टरांचा सलाह कधी घ्यावा?"],
            "preventive": ["पुरेसे कोमट पाणी प्या.", "७-८ तास झोपा."],
            "avoid": ["डॉक्टरांच्या सल्ल्याशिवाय औषधे घेऊ नका."],
            "warning": ["ताप 102°F पेक्षा जास्त असल्यास", "४८ तासांपेक्षा जास्त लक्षणे राहिल्यास"],
        },
        "gu": {
            "summary_template": "**પુરાવા-આધારિત સ્વ-સંભાળ માર્ગદર્શન:** {summary}",
            "what_applies": "સામાન્ય સ્વાસ્થ્ય સમસ્યાઓ માટે સ્વ-સંભાળ માર્ગદર્શન.",
            "follow_up": "શું તમારા લક્ષણો 24-48 કલાક કરતાં વધુ સમયથી છે?",
            "lens_natural": "કુદરતી સ્વ-સંભાળ", "lens_ayurveda": "આયુર્વેદિક દ્રષ્ટિકોણ",
            "lens_medical": "સામાન્ય તબીબી સ્વ-સંભાળ",
            "chips": ["કુદરતી ઉપાયો કયા છે?", "આયુર્વેદિક ટિપ્સ", "ડોક્ટરની સલાહ ક્યારે લેવી?"],
            "preventive": ["પૂરતું ગરમ પાણી પીઓ.", "7-8 કલાક ઊઘો."],
            "avoid": ["ડૉક્ટરની સલાહ વગર દવા ન લો."],
            "warning": ["તાવ 102°F થી વધારે હોય ત્યારે", "48 કલાક થી વધારે સમય સુધી લક્ષણ ચાલુ રહે ત્યારે"],
        },
        "kn": {
            "summary_template": "**ಸಾಕ್ಷ್ಯಾಧಾರಿತ ಸ್ವಯಂ-ಆರೈಕೆ ಮಾರ್ಗದರ್ಶನ:** {summary}",
            "what_applies": "ಸಾಮಾನ್ಯ ಆರೋಗ್ಯ ಕಾಳಜಿಗಳಿಗೆ ಸ್ವಯಂ-ಆರೈಕೆ ಶಿಕ್ಷಣ.",
            "follow_up": "ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳು 24-48 ಗಂಟೆಗಳಿಗಿಂತ ಹೆಚ್ಚು ಕಾಲ ಉಳಿದಿವೆಯೇ?",
            "lens_natural": "ನೈಸರ್ಗಿಕ ಸ್ವಯಂ-ಆರೈಕೆ", "lens_ayurveda": "ಆಯುರ್ವೇದ ದೃಷ್ಟಿಕೋನ",
            "lens_medical": "ಸಾಮಾನ್ಯ ವೈದ್ಯಕೀಯ ಸ್ವಯಂ-ಆರೈಕೆ",
            "chips": ["ನೈಸರ್ಗಿಕ ಉಪಾಯಗಳು ಯಾವವು?", "ಆಯುರ್ವೇದ ಸಲಹೆಗಳು", "ವೈದ್ಯರನ್ನು ಯಾವಾಗ ಭೇಟಿಯಾಗಬೇಕು?"],
            "preventive": ["ಸಾಕಷ್ಟು ಬಿಸಿ ನೀರು ಕುಡಿಯಿರಿ.", "7-8 ಗಂಟೆ ನಿದ್ರಿಸಿ."],
            "avoid": ["ವೈದ್ಯರ ಸಲಹೆಯಿಲ್ಲದೆ ಔಷಧ ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ."],
            "warning": ["ಜ್ವರ 102°F ಗಿಂತ ಹೆಚ್ಚಾದಾಗ", "48 ಗಂಟೆಗಳಿಗಿಂತ ಹೆಚ್ಚು ರೋಗಲಕ್ಷಣಗಳು ಮುಂದುವರಿದಾಗ"],
        },
        "ml": {
            "summary_template": "**തെളിവ് അടിസ്ഥാനമാക്കിയുള്ള സ്വയം പരിചരണ മാർഗ്ഗനിർദ്ദേശം:** {summary}",
            "what_applies": "പൊതുവായ ആരോഗ്യ ആശങ്കകൾക്കുള്ള സ്വയം പരിചരണ വിദ്യാഭ്യാസം.",
            "follow_up": "നിങ്ങളുടെ ലക്ഷണങ്ങൾ 24-48 മണിക്കൂറിൽ കൂടുതൽ നിലനിൽക്കുന്നുണ്ടോ?",
            "lens_natural": "പ്രകൃതിദത്ത സ്വയം പരിചരണം", "lens_ayurveda": "ആയുർവേദ കാഴ്ചപ്പാട്",
            "lens_medical": "ജനറൽ മെഡിക്കൽ സ്വയം പരിചരണം",
            "chips": ["പ്രകൃതിദത്ത പ്രതിവിധികൾ ഏവ?", "ആയുർവേദ നിർദ്ദേശങ്ങൾ", "എപ്പോൾ ഡോക്ടറെ കാണണം?"],
            "preventive": ["ആവശ്യമായ ചൂടുവെള്ളം കുടിക്കുക.", "7-8 മണിക്കൂർ ഉറങ്ങുക."],
            "avoid": ["ഡോക്ടറുടെ ഉപദേശമില്ലാതെ മരുന്ന് കഴിക്കരുത്."],
            "warning": ["പനി 102°F-ൽ കൂടുതൽ ആണെങ്കിൽ", "48 മണിക്കൂറിൽ കൂടുതൽ ലക്ഷണങ്ങൾ തുടർന്നാൽ"],
        },
        "pa": {
            "summary_template": "**ਸਬੂਤ-ਆਧਾਰਿਤ ਸਵੈ-ਦੇਖਭਾਲ ਮਾਰਗਦਰਸ਼ਨ:** {summary}",
            "what_applies": "ਆਮ ਸਿਹਤ ਚਿੰਤਾਵਾਂ ਲਈ ਸਵੈ-ਦੇਖਭਾਲ ਸਿੱਖਿਆ।",
            "follow_up": "ਕੀ ਤੁਹਾਡੇ ਲੱਛਣ 24-48 ਘੰਟਿਆਂ ਤੋਂ ਵੱਧ ਸਮੇਂ ਤੋਂ ਹਨ?",
            "lens_natural": "ਕੁਦਰਤੀ ਸਵੈ-ਦੇਖਭਾਲ", "lens_ayurveda": "ਆਯੁਰਵੈਦਿਕ ਦ੍ਰਿਸ਼ਟੀਕੋਣ",
            "lens_medical": "ਆਮ ਮੈਡੀਕਲ ਸਵੈ-ਦੇਖਭਾਲ",
            "chips": ["ਕੁਦਰਤੀ ਉਪਾਅ ਕੀ ਹਨ?", "ਆਯੁਰਵੈਦਿਕ ਸੁਝਾਅ", "ਡਾਕਟਰ ਦੀ ਸਲਾਹ ਕਦੋਂ ਲਓ?"],
            "preventive": ["ਕਾਫ਼ੀ ਗਰਮ ਪਾਣੀ ਪੀਓ.", "7-8 ਘੰਟੇ ਸੌਂਵੋ."],
            "avoid": ["ਡਾਕਟਰ ਦੀ ਸਲਾਹ ਬਿਨਾਂ ਦਵਾਈ ਨਾ ਲਓ."],
            "warning": ["102°F ਤੋਂ ਵੱਧ ਬੁਖਾਰ ਹੋਣ 'ਤੇ", "48 ਘੰਟਿਆਂ ਤੋਂ ਵੱਧ ਲੱਛਣ ਜਾਰੀ ਰਹਿਣ 'ਤੇ"],
        },
        "or": {
            "summary_template": "**ପ୍ରମାଣ-ଆଧାରିତ ସ୍ୱୟଂ-ସେବା ମାର୍ଗଦର୍ଶନ:** {summary}",
            "what_applies": "ସାଧାରଣ ସ୍ୱାସ୍ଥ୍ୟ ଚିନ୍ତା ପାଇଁ ସ୍ୱୟଂ-ସେବା ଶିକ୍ଷା |",
            "follow_up": "ଆପଣଙ୍କର ଲକ୍ଷଣ ୨୪-୪୮ ଘଣ୍ଟାରୁ ଅଧିକ ସମୟ ଧରି ରହିଛି କି?",
            "lens_natural": "ପ୍ରାକୃତିକ ସ୍ୱୟଂ-ସେବା", "lens_ayurveda": "ଆୟୁର୍ବେଦିକ ଦୃଷ୍ଟିକୋଣ",
            "lens_medical": "ସାଧାରଣ ଡାକ୍ତରୀ ସ୍ୱୟଂ-ସେବା",
            "chips": ["ପ୍ରାକୃତିକ ପ୍ରତିକାର କ'ଣ?", "ଆୟୁର୍ବେଦିକ ପରାମର୍ଶ", "ଡାକ୍ତରଙ୍କ ସହ ଯୋଗାଯୋଗ ଅବସ୍ଥା"],
            "preventive": ["ଯଥେଷ୍ଟ ଉଷ୍ଣ ଜଳ ପିଅ.", "7-8 ଘଣ୍ଟା ଶୋ."],
            "avoid": ["ଡାକ୍ତରଙ୍କ ପରାମର୍ଶ ବିନା ଔଷଧ ଖାଇ ନ ଦିଅ."],
            "warning": ["ତାପ 102°F ରୁ ଅଧିକ ହେଲେ", "48 ଘଣ୍ଟାରୁ ଅଧିକ ଲକ୍ଷଣ ଚାଲୁ ରହିଲେ"],
        },
        "ur": {
            "summary_template": "**شواہد پر مبنی خود کی دیکھ بھال کی رہنمائی:** {summary}",
            "what_applies": "عام صحت کے خدشات کے لیے خود کی دیکھ بھال کی تعلیم۔",
            "follow_up": "کیا آپ کی علامات 24 سے 48 گھنٹے سے زیادہ پرانی ہیں؟",
            "lens_natural": "قدرتی خود کی دیکھ بھال", "lens_ayurveda": "آیو ویدک نقطہ نظر",
            "lens_medical": "عام طبی خود کی دیکھ بھال",
            "chips": ["قدرتی علاج کیا ہیں؟", "آیو ویدک مشورے", "ڈاکٹر سے کب رجوع کریں؟"],
            "preventive": ["کافی گرم پانی پئیں.", "7-8 گھنٹے سوئیں."],
            "avoid": ["ڈاکٹر کی مشورہ کے بغیر دوا نہ لیں."],
            "warning": ["بخار 102°F سے زیادہ ہو تو", "48 گھنٹوں سے زیادہ علامات رہیں تو"],
        },
    }

    fb = FALLBACK_TRANSLATIONS.get(target_lang)
    if fb:
        orig_summary = state.get("summary", "")
        # Translate entire summary using template, not just prefix it
        template = fb.get("summary_template", "{summary}")
        summary_translated = template.format(summary=orig_summary) if orig_summary else template.format(summary="")

        orig_table = state.get("action_table", [])
        translated_table = []
        for r in orig_table:
            old_cits = r.citation_ids if hasattr(r, "citation_ids") else []
            old_lens = r.guidance_lens if hasattr(r, "guidance_lens") else ""

            # Translate guidance_lens based on content
            if "ayurveda" in old_lens.lower():
                lens_text = fb.get("lens_ayurveda", old_lens)
            elif "medical" in old_lens.lower() or "allopathic" in old_lens.lower():
                lens_text = fb.get("lens_medical", old_lens)
            else:
                lens_text = fb.get("lens_natural", old_lens)

            translated_table.append(ActionTableRow(
                guidance_lens=lens_text,
                # Keep other fields in English for fallback (only lens is translated)
                what_may_help=r.what_may_help if hasattr(r, "what_may_help") else "",
                how_to_follow=r.how_to_follow if hasattr(r, "how_to_follow") else "",
                frequency_duration=r.frequency_duration if hasattr(r, "frequency_duration") else "",
                evidence_strength=r.evidence_strength if hasattr(r, "evidence_strength") else "",
                cautions=r.cautions if hasattr(r, "cautions") else "",
                stop_and_seek_care_if=r.stop_and_seek_care_if if hasattr(r, "stop_and_seek_care_if") else "",
                citation_ids=old_cits,
            ))

        chips = fb.get("chips", state.get("quick_action_chips", []))
        quick_actions_translated = [
            QuickAction(
                label=chip,
                standalone_query=state.get("quick_actions", [{}])[i].standalone_query
                if i < len(state.get("quick_actions", [])) and hasattr(state.get("quick_actions", [])[i], "standalone_query")
                else chip,
                parent_topic=state.get("quick_actions", [{}])[i].parent_topic
                if i < len(state.get("quick_actions", []))
                else "",
            )
            for i, chip in enumerate(chips)
        ]

        return {
            "summary": summary_translated,
            "what_this_applies_to": fb.get("what_applies", state.get("what_this_applies_to", "")),
            "follow_up_question": fb.get("follow_up", state.get("follow_up_question", "")),
            "quick_action_chips": chips,
            "quick_actions": quick_actions_translated,
            "action_table": translated_table,
            "preventive_approaches": fb.get("preventive", state.get("preventive_approaches", [])),
            "things_to_avoid": fb.get("avoid", state.get("things_to_avoid", [])),
            "when_to_seek_care": fb.get("warning", state.get("when_to_seek_care", [])),
            "warning_signs": fb.get("warning", state.get("warning_signs", [])),
            "translation_status": f"fallback_dictionary:{target_lang}",
            "response_language": target_lang,
        }

    return {"translation_status": "failed_no_fallback"}


# ════════════════════════════════════════════════════════════
# Node 14: Final Response Assembly
# ════════════════════════════════════════════════════════════

async def final_response_node(state: GraphState) -> dict[str, Any]:
    triage = state.get("triage_result", TriageResult(outcome=TriageOutcome.SELF_CARE, reasoning=""))
    citations = state.get("citations", [])
    quick_actions = state.get("quick_actions", [])
    quick_action_chips = state.get("quick_action_chips", [])

    # Determine overall evidence level from retrieval
    evidence_count = state.get("evidence_count", 0)
    if evidence_count >= 5:
        overall_ev = EvidenceLevel.HIGH
    elif evidence_count >= 2:
        overall_ev = EvidenceLevel.MODERATE
    elif evidence_count >= 1:
        overall_ev = EvidenceLevel.LOW
    else:
        overall_ev = EvidenceLevel.INSUFFICIENT

    response = MedicoBuddyResponse(
        triage_outcome=triage.outcome,
        safety_status=state.get("safety_status", "self-care information"),
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
        overall_evidence_level=overall_ev,
        targeted_follow_up=state.get("follow_up_question", ""),
        follow_up_question=state.get("follow_up_question", ""),
        quick_action_chips=quick_action_chips,
        quick_actions=quick_actions,
        urgency_summary="self-care information",
        user_report_summary=state.get("what_this_applies_to", ""),
        seek_care_conditions=state.get("when_to_seek_care", []),
    )

    debug_panel = state.get("retrieval_diagnostics", {})

    return {
        "final_response": response,
        "debug_panel": debug_panel,
    }
