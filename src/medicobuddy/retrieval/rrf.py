"""Reciprocal Rank Fusion for combining pgvector and Milvus result lists."""

from __future__ import annotations

from typing import Any


def reciprocal_rank_fusion(
    *result_lists: list[dict[str, Any]],
    k: int = 60,
) -> list[dict[str, Any]]:
    """Merge multiple ranked result lists using Reciprocal Rank Fusion (RRF).

    RRF score = sum over lists of 1/(k + rank_in_list)

    Args:
        *result_lists: Each is a list of dicts with 'id' and 'score' keys.
        k: RRF constant (default 60 per Cormack et al. 2009).

    Returns:
        Deduplicated list sorted by descending RRF score.
    """
    rrf_scores: dict[str, float] = {}
    id_to_item: dict[str, dict[str, Any]] = {}

    for results in result_lists:
        for rank, item in enumerate(results, start=1):
            item_id = str(item.get("id", ""))
            if not item_id:
                continue
            rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + 1.0 / (k + rank)
            if item_id not in id_to_item:
                id_to_item[item_id] = item

    fused: list[dict[str, Any]] = []
    for item_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: -x[1]):
        item = dict(id_to_item[item_id])
        item["rrf_score"] = round(rrf_score, 6)
        item["original_score"] = item.get("score", 0.0)
        fused.append(item)

    return fused
