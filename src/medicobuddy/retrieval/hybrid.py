"""Hybrid retrieval combining graph traversal + vector similarity + BM25 with RRF.

Three-way fusion: vector (pgvector cosine) + BM25 (PostgreSQL tsvector) + graph (Neo4j).
"""

from __future__ import annotations

import logging
from typing import Any

from medicobuddy.knowledge_graph.queries import KnowledgeGraphQueries
from medicobuddy.retrieval.rrf import reciprocal_rank_fusion
from medicobuddy.retrieval.vector_store import VectorStoreClient

logger = logging.getLogger(__name__)

# Medical synonym dictionary for entity expansion
MEDICAL_SYNONYMS: dict[str, list[str]] = {
    "headache": ["cephalgia", "head pain", "migraine", "tension headache"],
    "stomach discomfort": ["dyspepsia", "indigestion", "abdominal pain", "stomach ache", "gastric discomfort"],
    "cold": ["common cold", "rhinitis", "upper respiratory infection", "URI", "coryza"],
    "cough": ["coughing", "tussis", "respiratory cough", "dry cough", "productive cough"],
    "fever": ["pyrexia", "elevated temperature", "febrile"],
    "nausea": ["queasiness", "feeling sick", "motion sickness", "emesis"],
    "fatigue": ["tiredness", "exhaustion", "lethargy", "malaise", "weariness"],
    "allergy": ["allergies", "allergic reaction", "hypersensitivity", "seasonal allergy", "hay fever"],
    "sinus congestion": ["sinusitis", "nasal congestion", "blocked nose", "sinus pressure"],
    "skin": ["dermatitis", "skin care", "skin irritation", "eczema", "rash"],
    "hair": ["hair care", "hair loss", "alopecia", "hair thinning"],
    "sleep": ["insomnia", "sleep hygiene", "sleep disorder", "restlessness"],
    "stress": ["anxiety", "tension", "mental stress", "emotional stress"],
    "dizziness": ["vertigo", "lightheadedness", "giddiness"],
}


def expand_with_synonyms(entity: str) -> list[str]:
    """Expand a medical entity with its synonyms."""
    entity_lower = entity.lower().strip()
    expanded = [entity_lower]

    for canonical, synonyms in MEDICAL_SYNONYMS.items():
        if entity_lower == canonical or entity_lower in synonyms:
            expanded.append(canonical)
            expanded.extend(synonyms)
            break
        # Partial match
        if canonical in entity_lower or entity_lower in canonical:
            expanded.append(canonical)
            expanded.extend(synonyms)
            break

    return list(set(expanded))


class HybridRetriever:
    """Combines graph traversal, vector similarity, and BM25 with RRF."""

    def __init__(
        self,
        graph_queries: KnowledgeGraphQueries,
        vector_store: VectorStoreClient,
    ) -> None:
        self._graph = graph_queries
        self._vector = vector_store

    async def retrieve(
        self,
        query: str,
        symptom_name: str = "",
        entities: list[str] | None = None,
        conditions: list[str] | None = None,
        top_k: int = 10,
    ) -> dict[str, Any]:
        """Perform hybrid retrieval for a symptom query.

        Three-way fusion: vector + BM25 + graph results.

        Args:
            query: Natural language query for vector + BM25 search.
            symptom_name: Structured symptom name for graph traversal.
            entities: Extracted entities for synonym-expanded graph queries.
            conditions: User's conditions for contraindication checking.
            top_k: Max results per source.

        Returns:
            Dict with graph_results, vector_results, bm25_results,
            fused_results, contraindications, and ayurvedic_concepts.
        """
        # ── Graph retrieval with synonym expansion ───────────
        graph_results: list[dict[str, Any]] = []
        contraindications: list[dict[str, Any]] = []
        ayurvedic_concepts: list[dict[str, Any]] = []

        search_entities = entities or ([symptom_name] if symptom_name else [])

        for entity in search_entities:
            expanded = expand_with_synonyms(entity)
            for term in expanded:
                try:
                    actions = await self._graph.get_safe_actions_for_symptom(term)
                    for a in actions:
                        if not any(g.get("action_id") == a.get("action_id") for g in graph_results):
                            graph_results.append({
                                "id": a.get("action_id", ""),
                                "text": a.get("description", ""),
                                "score": 1.0,
                                **a,
                            })
                except Exception:
                    logger.debug("Graph retrieval failed for entity '%s'", term)

            # Ayurvedic concepts
            try:
                concepts = await self._graph.get_ayurvedic_concepts_for_symptom(entity)
                ayurvedic_concepts.extend(concepts)
            except Exception:
                logger.debug("Ayurvedic concept retrieval failed for '%s'", entity)

        # Check contraindications for user conditions
        if conditions:
            for condition in conditions:
                try:
                    contras = await self._graph.get_contraindications_for_condition(condition)
                    contraindications.extend(contras)
                except Exception:
                    logger.debug("Contraindication check failed for %s", condition)

        # ── Vector + BM25 retrieval (handled by VectorStoreClient) ──
        vector_results: list[dict[str, Any]] = []
        bm25_results: list[dict[str, Any]] = []
        try:
            vector_results = await self._vector.search_vector_only(query, top_k=top_k * 2)
        except Exception:
            logger.warning("Vector retrieval failed", exc_info=True)

        try:
            bm25_results = await self._vector.search_bm25_only(query, top_k=top_k * 2)
        except Exception:
            logger.warning("BM25 retrieval failed", exc_info=True)

        # ── Three-way Reciprocal Rank Fusion ─────────────────
        non_empty_lists = [
            lst for lst in [vector_results, bm25_results, graph_results]
            if lst
        ]

        if len(non_empty_lists) > 1:
            fused = reciprocal_rank_fusion(*non_empty_lists, id_key="id")
        elif non_empty_lists:
            fused = non_empty_lists[0]
        else:
            fused = []

        return {
            "graph_results": graph_results,
            "vector_results": vector_results,
            "bm25_results": bm25_results,
            "fused_results": fused[:top_k],
            "contraindications": contraindications,
            "ayurvedic_concepts": ayurvedic_concepts,
        }
