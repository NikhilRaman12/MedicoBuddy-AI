"""VectorStoreRouter supporting PostgreSQL pgvector (Default) and Milvus (Optional)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from medicobuddy.config import Settings
from medicobuddy.retrieval.embeddings import get_embedding_provider

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NORM_DIR = PROJECT_ROOT / "evidence" / "normalized"

STOPWORDS = {
    "after", "since", "morning", "this", "work", "with", "have", "from", "that",
    "feel", "some", "your", "about", "today", "eating", "and", "the", "for", "mild"
}

SYMPTOM_KEYWORDS = [
    "headache", "stomach", "digestive", "indigestion", "dyspepsia", "cold",
    "cough", "respiratory", "fever", "fatigue", "allergy", "allergies", "sleep",
    "stress", "ayurveda", "diet", "activity", "safety"
]


class VectorStoreClient:
    """Vector store client supporting pgvector primary and Milvus optional secondary."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embedder = get_embedding_provider(settings)
        self._pg_pool: Any = None
        self._milvus_client: Any = None
        self._is_connected = False
        self.fingerprint = self._embedder._fingerprint

    async def connect(self) -> bool:
        """Initialize connections to pgvector (default) and Milvus (optional)."""
        NORM_DIR.mkdir(parents=True, exist_ok=True)

        if getattr(self._settings, "enable_pgvector", True):
            try:
                import asyncpg
                dsn = getattr(self._settings, "postgres_dsn", "postgresql://postgres:postgres@localhost:5432/medicobuddy").replace("+asyncpg", "")
                self._pg_pool = await asyncpg.create_pool(
                    dsn=dsn,
                    min_size=1,
                    max_size=5,
                    timeout=5,
                )
                async with self._pg_pool.acquire() as conn:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    await conn.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self._settings.milvus_collection} (
                            id VARCHAR(64) PRIMARY KEY,
                            embedding vector({self._embedder.dimension}),
                            text TEXT,
                            metadata JSONB,
                            fingerprint VARCHAR(32)
                        );
                        """
                    )
                logger.info("Connected to PostgreSQL pgvector primary DB")
                self._is_connected = True
            except Exception as exc:
                logger.info("PostgreSQL pgvector DB connection offline (%s) — operating in local vector store mode", exc)
                self._pg_pool = None

        if getattr(self._settings, "enable_milvus", False):
            try:
                from pymilvus import MilvusClient
                milvus_uri = getattr(self._settings, "milvus_uri", None) or f"http://{self._settings.milvus_host}:{self._settings.milvus_port}"
                self._milvus_client = MilvusClient(uri=milvus_uri)
                if not self._milvus_client.has_collection(self._settings.milvus_collection):
                    self._milvus_client.create_collection(
                        collection_name=self._settings.milvus_collection,
                        dimension=self._embedder.dimension,
                        metric_type="COSINE",
                        auto_id=False,
                        id_type="string",
                        max_length=64,
                    )
                logger.info("Connected to Milvus optional vector DB")
                self._is_connected = True
            except Exception as exc:
                logger.info("Milvus optional vector DB unavailable: %s", exc)
                self._milvus_client = None

        self._is_connected = True
        return self._is_connected

    async def is_ready(self) -> bool:
        return self._is_connected

    def get_total_indexed_chunks(self) -> int:
        if NORM_DIR.exists():
            return len(list(NORM_DIR.glob("*.json")))
        return 0

    async def upsert_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> bool:
        try:
            vector = self._embedder.embed_text(text, is_query=False)
        except Exception as exc:
            logger.error("Skipping upsert for %s — embedding failed: %s", doc_id, exc)
            return False

        point_id = doc_id or uuid4().hex
        metadata["embedding_fingerprint"] = self.fingerprint
        metadata["vector"] = vector

        n_file = NORM_DIR / f"{point_id}.json"
        n_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        success = True

        if self._pg_pool is not None:
            try:
                async with self._pg_pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        INSERT INTO {self._settings.milvus_collection} (id, embedding, text, metadata, fingerprint)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            text = EXCLUDED.text,
                            metadata = EXCLUDED.metadata,
                            fingerprint = EXCLUDED.fingerprint;
                        """,
                        point_id,
                        str(vector),
                        text,
                        json.dumps(metadata),
                        self.fingerprint,
                    )
            except Exception as exc:
                logger.warning("pgvector upsert failed for %s: %s", point_id, exc)

        if self._milvus_client is not None:
            try:
                data = [{"id": point_id, "vector": vector, "text": text, **metadata}]
                self._milvus_client.upsert(
                    collection_name=self._settings.milvus_collection,
                    data=data,
                )
            except Exception as exc:
                logger.warning("Milvus upsert failed for %s: %s", point_id, exc)

        return success

    async def search_similar(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.20,
    ) -> list[dict[str, Any]]:
        vector = self._embedder.embed_text(query, is_query=True)
        results: list[dict[str, Any]] = []

        query_words = [
            w.lower() for w in query.lower().split()
            if len(w) > 2 and w.lower() not in STOPWORDS
        ]
        matched_symptom_terms = [w for w in query_words if any(k in w for k in SYMPTOM_KEYWORDS)]

        # 1. pgvector Primary Search
        if self._pg_pool is not None:
            try:
                async with self._pg_pool.acquire() as conn:
                    rows = await conn.fetch(
                        f"""
                        SELECT id, text, metadata, 1 - (embedding <=> $1) AS score
                        FROM {self._settings.milvus_collection}
                        ORDER BY embedding <=> $1 ASC
                        LIMIT $2;
                        """,
                        str(vector),
                        top_k * 2,
                    )
                    for row in rows:
                        raw_score = float(row["score"])
                        if raw_score >= score_threshold:
                            meta = json.loads(row["metadata"]) if row["metadata"] else {}
                            if meta.get("retrieval_allowed", True):
                                results.append({
                                    "id": str(row["id"]),
                                    "score": raw_score,
                                    "text": row["text"] or "",
                                    "metadata": meta,
                                    "backend": "pgvector",
                                })
                if results:
                    return results[:top_k]
            except Exception as exc:
                logger.warning("pgvector search failed: %s", exc)

        # 2. Local normalized vector index search
        if NORM_DIR.exists():
            candidates: list[dict[str, Any]] = []
            for f_path in NORM_DIR.glob("*.json"):
                try:
                    meta = json.loads(f_path.read_text(encoding="utf-8"))
                    doc_vector = meta.get("vector")
                    if not doc_vector or len(doc_vector) != len(vector):
                        continue

                    # Calculate Cosine similarity
                    dot_product = sum(a * b for a, b in zip(vector, doc_vector))
                    norm_a = (sum(a * a for a in vector)) ** 0.5 or 1.0
                    norm_b = (sum(b * b for b in doc_vector)) ** 0.5 or 1.0
                    sim_score = dot_product / (norm_a * norm_b)

                    chunk_text = meta.get("text", "")
                    chunk_text_lower = chunk_text.lower()
                    source_file = meta.get("source_file", "").lower()

                    # Domain keyword relevance boost
                    if matched_symptom_terms:
                        if any(term in chunk_text_lower or term in source_file for term in matched_symptom_terms):
                            sim_score = min(1.0, sim_score + 0.65)

                    logger.info("Raw local vector score for %s (%s): %.4f", meta.get("chunk_id"), meta.get("source_file"), sim_score)

                    if sim_score >= score_threshold and meta.get("retrieval_allowed", True):
                        candidates.append({
                            "id": meta.get("chunk_id", f_path.stem),
                            "score": round(sim_score, 4),
                            "text": chunk_text,
                            "metadata": meta,
                            "backend": "local_vector_index",
                        })
                except Exception as exc:
                    logger.warning("Error reading vector chunk %s: %s", f_path, exc)

            candidates.sort(key=lambda x: x["score"], reverse=True)
            results = candidates[:top_k]

        return results

    async def close(self) -> None:
        if self._pg_pool is not None:
            try:
                await self._pg_pool.close()
            except Exception:
                pass
        if self._milvus_client is not None:
            try:
                self._milvus_client.close()
            except Exception:
                pass
        self._is_connected = False
