"""Hybrid retrieval combining graph traversal + vector similarity with RRF."""

from __future__ import annotations

import logging
from typing import Any

from medicobuddy.knowledge_graph.queries import KnowledgeGraphQueries
from medicobuddy.retrieval.vector_store import VectorStoreClient

logger = logging.getLogger(__name__)

# Reciprocal Rank Fusion constant
RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict[str, Any]]],
    id_key: str = "id",
    k: int = RRF_K,
) -> list[dict[str, Any]]:
    """Merge multiple ranked result lists using Reciprocal Rank Fusion.

    RRF score = Σ 1 / (k + rank_i) for each list where item appears.

    Args:
        ranked_lists: Multiple lists of results, each sorted by relevance.
        id_key: Key to use for identifying unique results.
        k: RRF constant (default 60).

    Returns:
        Merged list sorted by fused score, descending.
    """
    scores: dict[str, float] = {}
    items: dict[str, dict[str, Any]] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            item_id = str(item.get(id_key, rank))
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            if item_id not in items:
                items[item_id] = item

    # Sort by fused score
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)

    results = []
    for item_id in sorted_ids:
        item = items[item_id].copy()
        item["rrf_score"] = scores[item_id]
        results.append(item)

    return results


class HybridRetriever:
    """Combines graph traversal and vector similarity with RRF."""

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
        conditions: list[str] | None = None,
        top_k: int = 10,
    ) -> dict[str, Any]:
        """Perform hybrid retrieval for a symptom query.

        Args:
            query: Natural language query for vector search.
            symptom_name: Structured symptom name for graph traversal.
            conditions: User's conditions for contraindication checking.
            top_k: Max results per source.

        Returns:
            Dict with graph_results, vector_results, fused_results,
            contraindications, and ayurvedic_concepts.
        """
        # ── Graph retrieval ──────────────────────────────────
        graph_results: list[dict[str, Any]] = []
        contraindications: list[dict[str, Any]] = []
        ayurvedic_concepts: list[dict[str, Any]] = []

        if symptom_name:
            try:
                actions = await self._graph.get_safe_actions_for_symptom(symptom_name)
                graph_results = [
                    {"id": a.get("action_id", ""), "text": a.get("description", ""), **a}
                    for a in actions
                ]
            except Exception:
                logger.warning("Graph retrieval failed", exc_info=True)

            try:
                ayurvedic_concepts = await self._graph.get_ayurvedic_concepts_for_symptom(
                    symptom_name
                )
            except Exception:
                logger.warning("Ayurvedic concept retrieval failed", exc_info=True)

        # Check contraindications for user conditions
        if conditions:
            for condition in conditions:
                try:
                    contras = await self._graph.get_contraindications_for_condition(condition)
                    contraindications.extend(contras)
                except Exception:
                    logger.warning("Contraindication check failed for %s", condition)

        # ── Vector retrieval ─────────────────────────────────
        vector_results: list[dict[str, Any]] = []
        try:
            vector_results = await self._vector.search_similar(query, top_k=top_k)
        except Exception:
            logger.warning("Vector retrieval failed", exc_info=True)

        # ── Reciprocal Rank Fusion ───────────────────────────
        fused = reciprocal_rank_fusion(
            [graph_results, vector_results],
            id_key="id",
        )

        return {
            "graph_results": graph_results,
            "vector_results": vector_results,
            "fused_results": fused[:top_k],
            "contraindications": contraindications,
            "ayurvedic_concepts": ayurvedic_concepts,
        }
