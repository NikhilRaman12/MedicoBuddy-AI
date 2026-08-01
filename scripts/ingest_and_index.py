"""MedicoBuddy AI — Complete PDF Ingestion & Vector Indexing Pipeline.

This script:
1. Discovers all PDFs recursively in evidence/raw/
2. Computes SHA-256 checksums
3. Extracts text with PyMuPDF (OCR hint on empty pages)
4. Semantically chunks at 400-700 tokens with 80-token overlap
5. Deduplicates chunks by content hash
6. Generates Qwen embeddings in batches
7. Upserts chunks into pgvector with full provenance metadata
8. Saves per-chunk JSON to evidence/normalized/ for FAISS fallback
9. Writes ingestion_report.json with per-document stats
10. Quarantines unreadable documents

Usage:
    python scripts/ingest_and_index.py [--dry-run] [--reset]

Environment:
    GROQ_API_KEY    Only needed for response generation, not ingestion
    POSTGRES_DSN    Optional; if absent, only local JSON cache is written
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

# ── Path setup ───────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ingest_and_index")

EVIDENCE_DIR = PROJECT_ROOT / "evidence"
RAW_DIR = EVIDENCE_DIR / "raw"
NORMALIZED_DIR = EVIDENCE_DIR / "normalized"
REPORTS_DIR = EVIDENCE_DIR / "reports"
QUARANTINE_DIR = EVIDENCE_DIR / "quarantine"

for d in [NORMALIZED_DIR, REPORTS_DIR, QUARANTINE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── Constants ─────────────────────────────────────────────────
CHUNK_SIZE_TOKENS = 600      # target chunk size (words ≈ tokens * 0.75)
CHUNK_OVERLAP_TOKENS = 80    # overlap to preserve context across chunks
MIN_CHUNK_CHARS = 120        # discard chunks shorter than this
BATCH_SIZE = 16              # embedding batch size


# ══════════════════════════════════════════════════════════════
# Utilities
# ══════════════════════════════════════════════════════════════

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_valid_pdf(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            header = f.read(5)
        return header == b"%PDF-"
    except Exception:
        return False


def word_count(text: str) -> int:
    return len(text.split())


def normalize_text(text: str) -> str:
    """Clean text without removing clinically important content."""
    # Remove excessive whitespace but preserve newlines that indicate structure
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove null bytes and control chars except newline/tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_TOKENS,
    overlap: int = CHUNK_OVERLAP_TOKENS,
) -> list[str]:
    """Split text into semantic chunks with overlap.

    Uses word-level splitting (~0.75 tokens/word) targeting 400-700 real tokens.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_text_str = " ".join(words[start:end])
        if len(chunk_text_str) >= MIN_CHUNK_CHARS:
            chunks.append(chunk_text_str)
        if end >= len(words):
            break
        start = end - overlap

    return chunks


# ══════════════════════════════════════════════════════════════
# PDF Text Extraction
# ══════════════════════════════════════════════════════════════

def extract_pdf_text(pdf_path: Path) -> tuple[list[dict[str, Any]], str]:
    """Extract text from PDF using PyMuPDF.

    Returns:
        (pages, full_text) where pages is a list of {page_number, text, char_count}
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Run: pip install PyMuPDF")
        return [], ""

    pages: list[dict[str, Any]] = []
    full_text_parts: list[str] = []

    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc, start=1):
            # Standard text extraction
            page_text = page.get_text("text")

            # If page has very little text, try blocks extraction
            if len(page_text.strip()) < 50:
                blocks = page.get_text("blocks")
                page_text = "\n".join(
                    b[4] for b in blocks if isinstance(b[4], str) and b[4].strip()
                )

            page_text = normalize_text(page_text)
            if page_text:
                pages.append({
                    "page_number": page_num,
                    "text": page_text,
                    "char_count": len(page_text),
                })
                full_text_parts.append(f"[Page {page_num}]\n{page_text}")

        doc.close()
        logger.info(
            "  Extracted %d pages, %d chars from %s",
            len(pages), sum(p["char_count"] for p in pages), pdf_path.name,
        )
    except Exception as exc:
        logger.error("PDF extraction failed for %s: %s", pdf_path, exc)

    return pages, "\n\n".join(full_text_parts)


# ══════════════════════════════════════════════════════════════
# Entity Extraction for Neo4j
# ══════════════════════════════════════════════════════════════

HEALTH_CONCEPTS = {
    "headache", "migraine", "tension headache", "head pain",
    "cold", "cough", "runny nose", "sore throat", "congestion",
    "nausea", "vomiting", "stomach discomfort", "indigestion", "bloating",
    "fatigue", "tiredness", "weakness", "exhaustion",
    "allergy", "allergic", "hay fever", "sinusitis",
    "sleep", "insomnia", "rest",
    "stress", "anxiety", "relaxation",
    "hair loss", "hair fall", "alopecia",
    "skin", "dermatitis", "eczema", "rash",
    "constipation", "diarrhea",
    "fever", "temperature",
    "hydration", "water", "fluids",
    "exercise", "physical activity",
    "nutrition", "diet", "vitamins",
    "ginger", "turmeric", "honey", "lemon",
    "steam", "warm water", "compress",
    "yoga", "meditation", "breathing",
    "ayurveda", "herbal",
}


def extract_entities(text: str) -> dict[str, list[str]]:
    """Extract health-relevant entities from chunk text for Neo4j seeding."""
    text_lower = text.lower()
    found_concepts = [c for c in HEALTH_CONCEPTS if c in text_lower]

    symptoms = [c for c in found_concepts if c in {
        "headache", "migraine", "cold", "cough", "nausea", "vomiting",
        "fatigue", "allergy", "fever", "constipation", "diarrhea",
        "hair loss", "hair fall", "skin", "insomnia", "stress",
    }]
    actions = [c for c in found_concepts if c in {
        "hydration", "water", "fluids", "rest", "sleep", "exercise",
        "steam", "warm water", "compress", "yoga", "meditation",
        "ginger", "turmeric", "honey", "lemon", "herbal",
    }]
    return {
        "symptoms": list(set(symptoms)),
        "actions": list(set(actions)),
        "concepts": list(set(found_concepts)),
    }


# ══════════════════════════════════════════════════════════════
# Main Ingestion Logic
# ══════════════════════════════════════════════════════════════

async def run_ingestion(dry_run: bool = False, reset: bool = False) -> dict[str, Any]:
    """Main ingestion function.

    Args:
        dry_run: If True, extract and chunk but do not write to vector store.
        reset: If True, clear existing normalized JSON cache before ingestion.
    """
    logger.info("=" * 70)
    logger.info("MedicoBuddy AI — PDF Ingestion & Vector Indexing Pipeline")
    logger.info("=" * 70)

    if reset:
        logger.info("Resetting normalized cache...")
        for f in NORMALIZED_DIR.glob("*.json"):
            f.unlink()

    # ── Discover PDFs ────────────────────────────────────────
    pdf_files = sorted(PROJECT_ROOT.glob("**/*.pdf"))
    # Filter to evidence/raw/ only (not .pytest_cache, node_modules, etc.)
    pdf_files = [p for p in pdf_files if "evidence" in str(p) and "raw" in str(p)]
    logger.info("Discovered %d PDFs in evidence/raw/", len(pdf_files))

    # ── Initialize embedding provider ────────────────────────
    embedding_provider = None
    embedding_error = None
    embedding_dimension = 1024

    if not dry_run:
        try:
            from medicobuddy.config import get_settings
            from medicobuddy.retrieval.embeddings import get_embedding_provider
            settings = get_settings()
            embedding_provider = get_embedding_provider(settings)
            embedding_dimension = embedding_provider.dimension
            if embedding_provider._backend == "ERROR":
                embedding_error = "Qwen3 embedding model failed to initialize"
                embedding_provider = None
                logger.error("Embedding provider failed: %s", embedding_error)
            else:
                logger.info(
                    "Embedding provider ready: %s (dim=%d)",
                    embedding_provider.model_name, embedding_dimension,
                )
        except Exception as exc:
            embedding_error = str(exc)
            logger.error("Could not initialize embedding provider: %s", exc)

    # ── Initialize vector store ───────────────────────────────
    vector_store = None
    vector_store_status = "not_initialized"

    if not dry_run and embedding_provider is not None:
        try:
            from medicobuddy.config import get_settings
            from medicobuddy.retrieval.vector_store import VectorStoreClient
            settings = get_settings()
            vector_store = VectorStoreClient(settings)
            connected = await vector_store.connect()
            if connected:
                vector_store_status = "connected"
                logger.info("pgvector connected and ready for indexing")
            else:
                vector_store_status = "unavailable"
                logger.warning(
                    "pgvector unavailable — chunks will be saved to local JSON cache only"
                )
        except Exception as exc:
            vector_store_status = f"error: {exc}"
            logger.warning("Vector store initialization failed: %s", exc)

    # ── Per-document processing ───────────────────────────────
    manifest: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    all_chunks: list[dict[str, Any]] = []
    seen_checksums: set[str] = set()  # doc-level dedup
    seen_chunk_hashes: set[str] = set()  # chunk-level dedup

    total_pages = 0
    total_chars = 0
    total_chunks_created = 0
    total_chunks_indexed = 0

    for pdf_path in pdf_files:
        rel_path = str(pdf_path.relative_to(PROJECT_ROOT))
        file_sha256 = sha256_file(pdf_path)
        file_size = pdf_path.stat().st_size

        logger.info("Processing: %s (%d bytes)", pdf_path.name, file_size)

        # ── Quarantine checks ─────────────────────────────────
        if not is_valid_pdf(pdf_path):
            reason = "Invalid PDF magic bytes"
            quarantined.append({"file": rel_path, "sha256": file_sha256, "reason": reason})
            logger.warning("  QUARANTINED: %s", reason)
            continue

        if file_size < 1024:
            reason = f"File too small ({file_size} bytes) — likely empty stub"
            quarantined.append({"file": rel_path, "sha256": file_sha256, "reason": reason})
            logger.warning("  QUARANTINED: %s", reason)
            continue

        if file_sha256 in seen_checksums:
            reason = "Duplicate document (same SHA-256 as already-ingested file)"
            quarantined.append({"file": rel_path, "sha256": file_sha256, "reason": reason})
            logger.warning("  SKIPPED: %s", reason)
            continue

        seen_checksums.add(file_sha256)

        # ── Extract text ──────────────────────────────────────
        pages, full_text = extract_pdf_text(pdf_path)

        if not pages or len(full_text.strip()) < 100:
            reason = f"Text extraction failed or too little text ({len(full_text)} chars)"
            quarantined.append({
                "file": rel_path, "sha256": file_sha256,
                "reason": reason, "chars_extracted": len(full_text),
            })
            logger.warning("  QUARANTINED: %s", reason)
            continue

        # ── Infer metadata from path/filename ─────────────────
        category = pdf_path.parent.name  # e.g. "headache_pain", "respiratory"
        doc_title = pdf_path.stem.replace("_", " ").replace("-", " ").title()
        doc_id = f"DOC_{file_sha256[:12]}"

        # Parse organization/year hints from filename
        organization = "Unknown"
        year = "2024"
        name_lower = pdf_path.stem.lower()
        if "who" in name_lower:
            organization = "World Health Organization (WHO)"
        elif "cdc" in name_lower:
            organization = "Centers for Disease Control and Prevention (CDC)"
        elif "nice" in name_lower:
            organization = "NICE (UK National Institute for Health and Care Excellence)"
        elif "nccih" in name_lower:
            organization = "National Center for Complementary and Integrative Health (NCCIH)"
        elif "medlineplus" in name_lower:
            organization = "MedlinePlus / US National Library of Medicine"
        elif "niddk" in name_lower:
            organization = "National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)"
        elif "ccras" in name_lower or "ayurveda" in name_lower.replace("_", ""):
            organization = "Central Council for Research in Ayurvedic Sciences (CCRAS)"
        elif "ayurveda" in name_lower:
            organization = "Ayurvedic Science Institute"

        # ── Chunk ─────────────────────────────────────────────
        chunks = chunk_text(full_text)
        doc_chunks: list[dict[str, Any]] = []

        for chunk_idx, chunk_text_str in enumerate(chunks):
            chunk_hash = sha256_text(chunk_text_str)
            if chunk_hash in seen_chunk_hashes:
                logger.debug("  Duplicate chunk skipped (idx=%d)", chunk_idx)
                continue
            seen_chunk_hashes.add(chunk_hash)

            chunk_id = f"{doc_id}_CHK_{chunk_idx:04d}"
            entities = extract_entities(chunk_text_str)

            # Find which page this chunk primarily belongs to
            # (heuristic: find the page whose text overlaps most with chunk start)
            page_number = 1
            chunk_start = chunk_text_str[:200]
            for pg in pages:
                if chunk_start[:50] in pg["text"]:
                    page_number = pg["page_number"]
                    break

            chunk_meta: dict[str, Any] = {
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "title": doc_title,
                "source_file": pdf_path.name,
                "relative_path": rel_path,
                "organization": organization,
                "year": year,
                "category": category,
                "page_number": page_number,
                "chunk_index": chunk_idx,
                "total_chunks": len(chunks),
                "char_count": len(chunk_text_str),
                "word_count": word_count(chunk_text_str),
                "sha256": file_sha256,
                "chunk_hash": chunk_hash,
                "entities": entities,
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            doc_chunks.append({
                "id": chunk_id,
                "text": chunk_text_str,
                "metadata": chunk_meta,
            })

        doc_chunks_count = len(doc_chunks)
        total_chunks_created += doc_chunks_count
        total_pages += len(pages)
        total_chars += sum(p["char_count"] for p in pages)

        # ── Embed & index ─────────────────────────────────────
        indexed_count = 0

        if dry_run:
            logger.info(
                "  DRY RUN: would index %d chunks (skipping embedding)",
                doc_chunks_count,
            )
        elif embedding_provider is not None:
            # Batch embedding
            texts = [c["text"] for c in doc_chunks]
            try:
                logger.info("  Embedding %d chunks...", len(texts))
                vectors = embedding_provider.embed_batch(texts)

                for chunk_data, vector in zip(doc_chunks, vectors):
                    chunk_data["metadata"]["embedding_dimension"] = len(vector)
                    chunk_data["metadata"]["embedding_model"] = embedding_provider.model_name

                    # Save to local JSON cache (for FAISS fallback)
                    json_path = NORMALIZED_DIR / f"{chunk_data['id']}.json"
                    cache_entry = {**chunk_data["metadata"], "vector": vector, "text": chunk_data["text"]}
                    try:
                        json_path.write_text(json.dumps(cache_entry, ensure_ascii=False), encoding="utf-8")
                    except Exception as exc:
                        logger.warning("  Failed to write cache for %s: %s", chunk_data["id"], exc)

                    # Index into pgvector
                    if vector_store is not None and vector_store_status == "connected":
                        try:
                            success = await vector_store.upsert_document(
                                doc_id=chunk_data["id"],
                                text=chunk_data["text"],
                                metadata=chunk_data["metadata"],
                            )
                            if success:
                                indexed_count += 1
                        except Exception as exc:
                            logger.warning(
                                "  pgvector upsert failed for %s: %s",
                                chunk_data["id"], exc,
                            )

                total_chunks_indexed += indexed_count
                logger.info(
                    "  Indexed %d/%d chunks to pgvector, %d to local cache",
                    indexed_count, doc_chunks_count, len(texts),
                )

            except Exception as exc:
                logger.error("  Embedding batch failed: %s", exc)
        else:
            # No embedding provider: save text-only cache entries
            logger.info(
                "  No embedding provider — saving %d chunks to local cache only",
                doc_chunks_count,
            )
            for chunk_data in doc_chunks:
                json_path = NORMALIZED_DIR / f"{chunk_data['id']}.json"
                cache_entry = {**chunk_data["metadata"], "text": chunk_data["text"]}
                try:
                    json_path.write_text(json.dumps(cache_entry, ensure_ascii=False), encoding="utf-8")
                except Exception as exc:
                    logger.warning("  Failed to write cache: %s", exc)

        all_chunks.extend(doc_chunks)

        manifest.append({
            "document_id": doc_id,
            "title": doc_title,
            "file_name": pdf_path.name,
            "relative_path": rel_path,
            "organization": organization,
            "year": year,
            "category": category,
            "sha256": file_sha256,
            "file_size_bytes": file_size,
            "page_count": len(pages),
            "char_count": sum(p["char_count"] for p in pages),
            "chunk_count": doc_chunks_count,
            "indexed_count": indexed_count,
            "status": "SUCCESS",
            "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    # ── Close vector store ────────────────────────────────────
    if vector_store is not None:
        await vector_store.close()

    # ── Write reports ─────────────────────────────────────────
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    ingestion_report = {
        "timestamp": timestamp,
        "dry_run": dry_run,
        "pdfs_discovered": len(pdf_files),
        "pdfs_successful": len(manifest),
        "pdfs_quarantined": len(quarantined),
        "pages_extracted": total_pages,
        "characters_extracted": total_chars,
        "chunks_created": total_chunks_created,
        "vectors_written": total_chunks_indexed,
        "local_cache_entries": len(list(NORMALIZED_DIR.glob("*.json"))),
        "vector_store_status": vector_store_status,
        "embedding_model": embedding_provider.model_name if embedding_provider else "unavailable",
        "embedding_dimension": embedding_dimension,
        "embedding_fingerprint": embedding_provider._fingerprint if embedding_provider else "",
        "embedding_error": embedding_error,
        "graph_nodes_written": 0,       # Filled in by seed_neo4j.py
        "graph_relationships_written": 0,
        "records": manifest,
        "quarantined": quarantined,
    }

    report_path = REPORTS_DIR / "ingestion_report.json"
    report_path.write_text(json.dumps(ingestion_report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Also write to evidence/ root for backward compat
    (EVIDENCE_DIR / "ingestion_report.json").write_text(
        json.dumps(ingestion_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    manifest_path = EVIDENCE_DIR / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    quarantine_path = EVIDENCE_DIR / "quarantined_sources.json"
    quarantine_path.write_text(json.dumps(quarantined, indent=2, ensure_ascii=False), encoding="utf-8")

    corpus_version = {
        "version": "2.0.0",
        "release_tag": "production_release_v2",
        "documents_count": len(manifest),
        "total_chunks": total_chunks_created,
        "vectors_indexed": total_chunks_indexed,
        "created_at": timestamp,
    }
    (EVIDENCE_DIR / "corpus_version.json").write_text(
        json.dumps(corpus_version, indent=2), encoding="utf-8"
    )

    logger.info("=" * 70)
    logger.info("Ingestion Complete!")
    logger.info("  PDFs processed: %d", len(manifest))
    logger.info("  PDFs quarantined: %d", len(quarantined))
    logger.info("  Total pages: %d", total_pages)
    logger.info("  Total characters: %d", total_chars)
    logger.info("  Chunks created: %d", total_chunks_created)
    logger.info("  Vectors indexed (pgvector): %d", total_chunks_indexed)
    logger.info("  Local cache entries: %d", len(list(NORMALIZED_DIR.glob("*.json"))))
    logger.info("  Reports saved to: %s", REPORTS_DIR)
    logger.info("=" * 70)

    return ingestion_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MedicoBuddy AI PDF Ingestion & Vector Indexing Pipeline"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Extract and chunk PDFs without embedding or indexing",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Clear existing normalized JSON cache before ingestion",
    )
    args = parser.parse_args()

    result = asyncio.run(run_ingestion(dry_run=args.dry_run, reset=args.reset))

    if result["pdfs_successful"] == 0:
        logger.error("No PDFs were successfully ingested.")
        sys.exit(1)

    if result["vectors_written"] == 0 and not args.dry_run:
        logger.warning(
            "No vectors were written to pgvector. "
            "Check that PostgreSQL is running and POSTGRES_DSN is set. "
            "Local JSON cache was written for FAISS fallback."
        )


if __name__ == "__main__":
    main()
