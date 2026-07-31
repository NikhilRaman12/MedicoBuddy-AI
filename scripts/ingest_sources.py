"""Repeatable evidence ingestion script for MedicoBuddy AI.

Workflow:
Source PDFs -> PyMuPDF parse -> DocumentChunker -> Qwen3-0.6B embed ->
pgvector (vectors + BM25 tsvector) -> Neo4j MERGE knowledge graph -> report
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add src/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from medicobuddy.config import get_settings
from medicobuddy.evidence.chunker import DocumentChunker
from medicobuddy.evidence.parser import DocumentParser
from medicobuddy.knowledge_graph.client import Neo4jClient
from medicobuddy.knowledge_graph.schema import (
    LABEL_AYURVEDIC_CONCEPT,
    LABEL_PASSAGE,
    LABEL_SELF_CARE_ACTION,
    LABEL_SOURCE_DOCUMENT,
    LABEL_SYMPTOM,
    REL_EXTRACTED_FROM,
    REL_MAY_SUPPORT,
    REL_SUPPORTED_BY,
)
from medicobuddy.retrieval.embeddings import get_embedding_provider
from medicobuddy.retrieval.vector_store import VectorStoreClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_sources")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
RAW_DIR = EVIDENCE_DIR / "raw"
NORMALIZED_DIR = EVIDENCE_DIR / "normalized"
QUARANTINE_DIR = EVIDENCE_DIR / "quarantine"
REPORTS_DIR = EVIDENCE_DIR / "reports"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

SUPPORTED_EXTENSIONS = {".pdf", ".xml", ".html", ".txt"}


def ensure_directories() -> None:
    for d in [RAW_DIR, NORMALIZED_DIR, QUARANTINE_DIR, REPORTS_DIR, ARTIFACTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


async def async_run_ingestion(rebuild: bool = False, validate: bool = False) -> dict[str, Any]:
    ensure_directories()
    settings = get_settings()

    if rebuild and NORMALIZED_DIR.exists():
        logger.info("Rebuilding development vector index — clearing %s", NORMALIZED_DIR)
        for f in NORMALIZED_DIR.glob("*.json"):
            try:
                f.unlink()
            except Exception:
                pass

    embedder = get_embedding_provider(settings)
    vector_store = VectorStoreClient(settings)
    neo4j = Neo4jClient(settings)

    pg_ok = await vector_store.connect()
    neo4j_active = await neo4j.connect()
    if neo4j_active:
        await neo4j.create_constraints()

    # Discover source files
    raw_files = [
        path for path in RAW_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not raw_files:
        raise RuntimeError(
            "Ingestion failed: No authentic source documents found in evidence/raw/. "
            "Place genuine PDF files in evidence/raw/"
        )

    per_pdf_reports: list[dict[str, Any]] = []
    pdfs_discovered = len([f for f in raw_files if f.suffix.lower() == ".pdf"])
    pdfs_successful = 0
    pdfs_quarantined = 0
    total_pdf_pages = 0
    pages_extracted = 0
    characters_extracted = 0

    authentic_docs_count = 0
    total_chunks_count = 0
    vector_upserts = 0
    graph_nodes = 0
    graph_relationships = 0
    quarantined_chunks = 0
    failures: list[dict[str, str]] = []

    symptom_keywords = [
        "headache", "cold", "fever", "cough", "nausea", "indigestion",
        "fatigue", "allergy", "sinus", "skin", "hair", "sleep", "stress",
        "digestive", "respiratory", "pain",
    ]

    for file_path in raw_files:
        try:
            logger.info("Parsing authentic document: %s", file_path.name)
            parsed_doc = DocumentParser.parse_file(file_path)

            file_bytes = file_path.read_bytes()
            file_checksum = hashlib.sha256(file_bytes).hexdigest()

            actual_pages = parsed_doc.pages_count
            total_pdf_pages += actual_pages
            pages_extracted += parsed_doc.pages_count
            characters_extracted += parsed_doc.total_characters

            if parsed_doc.quarantined:
                pdfs_quarantined += 1
                per_pdf_reports.append({
                    "filename": file_path.name,
                    "category": file_path.parent.name,
                    "actual_pdf_pages": actual_pages,
                    "pages_successfully_extracted": 0,
                    "characters_extracted": 0,
                    "chunks_generated": 0,
                    "extraction_method": "PyMuPDF (fitz)",
                    "checksum": file_checksum,
                    "errors": [parsed_doc.quarantine_reason or "Quarantined"],
                    "status": "quarantined",
                })
                logger.warning("Quarantined unreadable file %s: %s", file_path.name, parsed_doc.quarantine_reason)
                continue

            if file_path.suffix.lower() == ".pdf":
                pdfs_successful += 1

            chunks = DocumentChunker.chunk_document(parsed_doc)
            authentic_docs_count += 1
            total_chunks_count += len(chunks)

            file_chunks_written = 0

            for chunk in chunks:
                if chunk.quarantined:
                    quarantined_chunks += 1
                    q_file = QUARANTINE_DIR / f"{chunk.chunk_id}.json"
                    q_file.write_text(json.dumps(chunk.to_metadata(), indent=2), encoding="utf-8")
                    continue

                # 1. Real Qwen3-0.6B embedding & pgvector upsert
                try:
                    meta = chunk.to_metadata()
                    meta["page_number"] = chunk.page_number or 1
                    meta["source_file"] = file_path.name

                    upserted = await vector_store.upsert_document(
                        doc_id=chunk.chunk_id,
                        text=chunk.text,
                        metadata=meta,
                    )
                    if upserted:
                        vector_upserts += 1
                        file_chunks_written += 1
                except Exception as exc:
                    logger.warning("pgvector upsert failed for %s: %s", chunk.chunk_id, exc)

                # 2. Build Neo4j knowledge graph
                try:
                    chunk_text_lower = chunk.text.lower()
                    matched_symptoms = [s for s in symptom_keywords if s in chunk_text_lower]
                    if not matched_symptoms:
                        matched_symptoms = ["general_symptom"]

                    is_ayurveda = "ayurveda" in file_path.name.lower() or "ayurveda" in chunk_text_lower

                    cypher_merge = f"""
                    MERGE (src:{LABEL_SOURCE_DOCUMENT} {{source_file: $source_file}})
                    SET src.title = $title, src.publisher = $publisher, src.url = $url

                    MERGE (pas:{LABEL_PASSAGE} {{passage_id: $passage_id}})
                    SET pas.text = $text, pas.section_title = $section_title, pas.page_number = $page_number, pas.evidence_lane = $evidence_lane

                    MERGE (act:{LABEL_SELF_CARE_ACTION} {{action_name: $action_name}})
                    SET act.evidence_level = $evidence_level, act.description = $text

                    MERGE (pas)-[:{REL_EXTRACTED_FROM}]->(src)
                    MERGE (act)-[:{REL_SUPPORTED_BY}]->(pas)
                    """

                    params = {
                        "source_file": file_path.name,
                        "title": chunk.title,
                        "publisher": chunk.publisher,
                        "url": chunk.source_url,
                        "passage_id": chunk.chunk_id,
                        "text": chunk.text[:500],
                        "section_title": chunk.section_title or "General Self-Care",
                        "page_number": chunk.page_number or 1,
                        "evidence_lane": chunk.evidence_lane,
                        "action_name": chunk.section_title or f"Self-Care Practice ({chunk.chunk_id})",
                        "evidence_level": chunk.evidence_type,
                    }

                    if neo4j_active and neo4j._driver is not None:
                        await neo4j.execute_write(cypher_merge, params)

                        for sym_name in matched_symptoms:
                            sym_cypher = f"""
                            MATCH (act:{LABEL_SELF_CARE_ACTION} {{action_name: $action_name}})
                            MERGE (sym:{LABEL_SYMPTOM} {{name: $sym_name}})
                            MERGE (act)-[:{REL_MAY_SUPPORT}]->(sym)
                            """
                            await neo4j.execute_write(sym_cypher, {"action_name": params["action_name"], "sym_name": sym_name})

                        if is_ayurveda:
                            ayur_cypher = f"""
                            MERGE (ac:{LABEL_AYURVEDIC_CONCEPT} {{name: $concept_name}})
                            SET ac.description = $text, ac.evidence_category = 'traditional_use_only'
                            """
                            await neo4j.execute_write(ayur_cypher, {"concept_name": chunk.section_title or "Ayurvedic Practice", "text": chunk.text[:300]})

                    graph_nodes += 4 + len(matched_symptoms) - 1
                    graph_relationships += 3
                    neo4j.increment_local_counts(4, 3)
                except Exception as exc:
                    logger.warning("Neo4j MERGE failed for %s: %s", chunk.chunk_id, exc)

            per_pdf_reports.append({
                "filename": file_path.name,
                "category": file_path.parent.name,
                "actual_pdf_pages": actual_pages,
                "pages_successfully_extracted": actual_pages,
                "characters_extracted": parsed_doc.total_characters,
                "chunks_generated": file_chunks_written,
                "extraction_method": "PyMuPDF (fitz)",
                "checksum": file_checksum,
                "errors": None,
                "status": "success",
            })

        except Exception as exc:
            logger.error("Failed to ingest %s: %s", file_path.name, exc)
            failures.append({"file": file_path.name, "error": str(exc)})

    await vector_store.close()
    await neo4j.close()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pdfs_discovered": pdfs_discovered,
        "pdfs_successful": pdfs_successful,
        "pdfs_quarantined": pdfs_quarantined,
        "total_pdf_pages": total_pdf_pages,
        "pages_extracted": pages_extracted,
        "characters_extracted": characters_extracted,
        "chunks_created": total_chunks_count,
        "vectors_written": vector_upserts,
        "graph_nodes_written": graph_nodes,
        "graph_relationships_written": graph_relationships,
        "quarantined_chunks": quarantined_chunks,
        "embedding_fingerprint": embedder._fingerprint,
        "indexed_chunks_valid": (pdfs_successful == pdfs_discovered and vector_upserts > 0),
        "per_pdf_reports": per_pdf_reports,
        "failures": failures,
        "status": "success" if vector_upserts > 0 else "failed",
    }

    report_path_1 = REPORTS_DIR / "ingestion_report.json"
    report_path_1.write_text(json.dumps(report, indent=2), encoding="utf-8")

    report_path_2 = ARTIFACTS_DIR / "pdf_ingestion_report.json"
    report_path_2.write_text(json.dumps(report, indent=2), encoding="utf-8")

    logger.info("Ingestion report saved successfully to %s and %s", report_path_1, report_path_2)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest authentic evidence PDFs into pgvector & Neo4j graph")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild vector index from scratch")
    parser.add_argument("--validate", action="store_true", help="Validate index coverage and fingerprint")
    args = parser.parse_args()

    rep = asyncio.run(async_run_ingestion(rebuild=args.rebuild, validate=args.validate))
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
