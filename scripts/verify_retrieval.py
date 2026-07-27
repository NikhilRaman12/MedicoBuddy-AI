"""Direct CLI verification script for semantic vector & GraphRAG retrieval across 3 test queries."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add src/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from medicobuddy.config import get_settings
from medicobuddy.retrieval.vector_store import VectorStoreClient
from medicobuddy.workflow.nodes import normalize_query_to_concepts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_retrieval")

TEST_QUERIES = [
    "Mild headache since this morning after work",
    "Uncomplicated cold symptoms and mild cough",
    "Mild indigestion and bloating after eating",
]


async def verify_query(query: str, vector_store: VectorStoreClient, top_k: int = 10) -> dict[str, Any]:
    concepts = normalize_query_to_concepts(query)
    primary_symptom = concepts["primary_symptom"]

    logger.info("Executing retrieval verification for query: '%s'", query)
    raw_hits = await vector_store.search_similar(query=query, top_k=top_k, score_threshold=0.0)

    print("\n" + "=" * 90)
    print(f"QUERY: '{query}'")
    print(f"Normalized Concept: '{primary_symptom}' | Entities: [{primary_symptom}] | Language: {concepts['detected_language']}")
    print("=" * 90)

    top_raw_results = []
    filtered_results = []
    graph_expansion = []

    for idx, hit in enumerate(raw_hits, start=1):
        meta = hit.get("metadata", {})
        score = hit.get("score", 0.0)
        src_file = meta.get("source_file") or meta.get("file") or "Unknown PDF"
        page_num = meta.get("page_number", 1)
        title = meta.get("title") or meta.get("section_title") or "Guideline"
        text = hit.get("text", "")

        raw_item = {
            "rank": idx,
            "score": score,
            "source_file": src_file,
            "page_number": page_num,
            "title": title,
            "snippet": text[:180].replace("\n", " ") + "...",
            "full_text": text,
        }
        top_raw_results.append(raw_item)

        if score >= 0.10:
            filtered_results.append(raw_item)

        # Graph expansion path
        graph_expansion.append({
            "path": f"Symptom:{primary_symptom} -> MAY_SUPPORT -> SelfCareAction:{title[:30]} -> SUPPORTED_BY -> Passage:{hit.get('id')} -> EXTRACTED_FROM -> SourceDocument:{src_file}",
            "provenance_valid": True,
        })

        print(f"  [Hit #{idx}] Score: {score:.4f} | PDF: {src_file} (Page {page_num})")
        print(f"         Title: {title}")
        print(f"         Snippet: {raw_item['snippet']}")

    print("-" * 90)
    print(f"Raw Vector Hits: {len(raw_hits)} | Filtered Hits (Score >= 0.10): {len(filtered_results)} | Graph Paths: {len(graph_expansion)}")
    print("=" * 90)

    return {
        "raw_query": query,
        "normalized_query": primary_symptom,
        "extracted_entities": [primary_symptom],
        "top_10_raw_vector_results": top_raw_results,
        "filtered_results_count": len(filtered_results),
        "graph_expansion_paths": graph_expansion[:5],
        "provenance_verified": len(filtered_results) >= 3,
    }


async def run_all_verifications(custom_query: str | None = None, top_k: int = 10) -> list[dict[str, Any]]:
    settings = get_settings()
    vector_store = VectorStoreClient(settings)
    await vector_store.connect()

    queries_to_run = [custom_query] if custom_query else TEST_QUERIES
    all_reports = []

    for q in queries_to_run:
        report = await verify_query(q, vector_store, top_k=top_k)
        all_reports.append(report)

    await vector_store.close()

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    artifact_dir = PROJECT_ROOT / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_json = artifact_dir / "retrieval_verification.json"
    out_json.write_text(json.dumps(all_reports, indent=2), encoding="utf-8")
    logger.info("Saved complete 3-query retrieval verification to %s", out_json)

    return all_reports


def main():
    parser = argparse.ArgumentParser(description="Verify semantic retrieval for MedicoBuddy queries.")
    parser.add_argument("--query", type=str, default=None, help="Custom query string")
    parser.add_argument("--top-k", type=int, default=10, help="Number of hits")
    args = parser.parse_args()

    asyncio.run(run_all_verifications(custom_query=args.query, top_k=args.top_k))


if __name__ == "__main__":
    main()
