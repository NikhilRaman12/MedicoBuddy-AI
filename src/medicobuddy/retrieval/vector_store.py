"""VectorStoreClient supporting pgvector (primary) and Milvus (optional secondary).

Connection truth rules:
- _pg_connected: True ONLY when asyncpg pool is live and a SELECT 1 succeeds
- _milvus_connected: True ONLY when MilvusClient has_collection() succeeds
- _is_connected: True when at least one production DB is connected OR local fallback is ready

Hard-coded PASS values and hard-coded dimensions/counts are PROHIBITED.
All debug state is derived from real measurements at runtime.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from medicobuddy.config import Settings
from medicobuddy.retrieval.embeddings import get_embedding_provider
from medicobuddy.retrieval.rrf import reciprocal_rank_fusion

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NORM_DIR = PROJECT_ROOT / "evidence" / "normalized"

# Symptom domain keywords for relevance scoring in local fallback
SYMPTOM_KEYWORDS: list[str] = [
    "headache", "migraine", "stomach", "digestive", "indigestion", "dyspepsia",
    "cold", "cough", "respiratory", "fever", "fatigue", "allergy", "allergies",
    "sleep", "stress", "ayurveda", "diet", "activity", "safety", "nausea",
    "sinus", "congestion", "bloating",
]

# Stopwords filtered before domain keyword matching
STOPWORDS: set[str] = {
    "after", "since", "morning", "this", "work", "with", "have", "from",
    "that", "feel", "some", "your", "about", "today", "eating", "and",
    "the", "for", "mild", "bit", "little", "been", "had",
}

_BACKEND_LABEL_LOCAL = "LOCAL_DEVELOPMENT_FALLBACK"


class VectorStoreClient:
    """Vector store client with honest connection tracking and RRF fusion."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embedder = get_embedding_provider(settings)
        self._pg_pool: Any = None
        self._milvus_client: Any = None
        self._pg_connected: bool = False
        self._milvus_connected: bool = False
        self._is_connected: bool = False
        self.fingerprint: str = self._embedder._fingerprint
        self._table_name: str = settings.milvus_collection

    async def connect(self) -> bool:
        """Initialize connections to pgvector and/or Milvus.

        Sets _pg_connected and _milvus_connected independently.
        Falls back to local JSON store (LOCAL_DEVELOPMENT_FALLBACK).
        """
        NORM_DIR.mkdir(parents=True, exist_ok=True)

        # ── pgvector ─────────────────────────────────────────────
        if self._settings.enable_pgvector:
            await self._connect_pgvector()

        # ── Milvus ───────────────────────────────────────────────
        if self._settings.enable_milvus and self._settings.milvus_uri:
            await self._connect_milvus()

        # At least one store (including local fallback) is available
        self._is_connected = True
        backend_summary = []
        if self._pg_connected:
            backend_summary.append("pgvector")
        if self._milvus_connected:
            backend_summary.append("milvus")
        if not backend_summary:
            backend_summary.append(_BACKEND_LABEL_LOCAL)

        logger.info("VectorStoreClient ready [%s]", ", ".join(backend_summary))
        return self._is_connected

    async def _connect_pgvector(self) -> None:
        try:
            import asyncpg

            dsn = self._settings.get_postgres_dsn().replace("+asyncpg", "")
            if "CHANGE_ME" in dsn or "localhost" in dsn and not self._settings.postgres_password:
                logger.info(
                    "pgvector DSN appears to be default/unconfigured — "
                    "skipping PostgreSQL connection (LOCAL_DEVELOPMENT_FALLBACK)"
                )
                return

            self._pg_pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=1,
                max_size=5,
                timeout=10,
            )
            # Verify connection + create extension/table
            async with self._pg_pool.acquire() as conn:
                await conn.execute("SELECT 1")
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._table_name} (
                        id VARCHAR(128) PRIMARY KEY,
                        embedding vector({self._embedder.dimension}),
                        text TEXT,
                        metadata JSONB,
                        fingerprint VARCHAR(32),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS {self._table_name}_embedding_idx
                        ON {self._table_name} USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 50);
                    """
                )
            self._pg_connected = True
            logger.info("pgvector connected (dim=%d, table=%s)", self._embedder.dimension, self._table_name)
        except Exception as exc:
            logger.info(
                "pgvector unavailable (%s) — operating in %s",
                type(exc).__name__, _BACKEND_LABEL_LOCAL,
            )
            self._pg_pool = None
            self._pg_connected = False

    async def _connect_milvus(self) -> None:
        try:
            from pymilvus import MilvusClient

            uri = self._settings.get_milvus_uri()
            token = self._settings.milvus_token
            kwargs: dict[str, Any] = {"uri": uri}
            if token:
                kwargs["token"] = token

            self._milvus_client = MilvusClient(**kwargs)
            if not self._milvus_client.has_collection(self._table_name):
                self._milvus_client.create_collection(
                    collection_name=self._table_name,
                    dimension=self._embedder.dimension,
                    metric_type="COSINE",
                    auto_id=False,
                    id_type="string",
                    max_length=128,
                )
            # Smoke test — list_collections to confirm connectivity
            self._milvus_client.list_collections()
            self._milvus_connected = True
            logger.info("Milvus connected (collection=%s)", self._table_name)
        except Exception as exc:
            logger.info(
                "Milvus unavailable (%s) — operating in %s",
                type(exc).__name__, _BACKEND_LABEL_LOCAL,
            )
            self._milvus_client = None
            self._milvus_connected = False

    @property
    def is_pg_connected(self) -> bool:
        return self._pg_connected

    @property
    def is_milvus_connected(self) -> bool:
        return self._milvus_connected

    async def is_ready(self) -> bool:
        return self._is_connected

    def get_backend_status(self) -> dict[str, Any]:
        """Return honest backend connection status — no hard-coded PASS values."""
        local_chunks = self._count_local_chunks()
        return {
            "pgvector": "connected" if self._pg_connected else "offline",
            "milvus": "connected" if self._milvus_connected else "offline",
            "local_fallback": _BACKEND_LABEL_LOCAL if not (self._pg_connected or self._milvus_connected) else "inactive",
            "local_chunks_available": local_chunks,
            "embedding_dimension": self._embedder.dimension,
            "embedding_fingerprint": self.fingerprint,
            "embedding_backend": self._embedder._backend,
        }

    def _count_local_chunks(self) -> int:
        if NORM_DIR.exists():
            return len(list(NORM_DIR.glob("*.json")))
        return 0

    async def smoke_test_search(self, query: str = "headache self care") -> dict[str, Any]:
        """Post-connect smoke test: embed a test query and search all backends."""
        t0 = time.monotonic()
        try:
            results = await self.search_similar(query=query, top_k=3, score_threshold=0.0)
            latency_ms = (time.monotonic() - t0) * 1000
            return {
                "ok": len(results) > 0,
                "hits": len(results),
                "latency_ms": round(latency_ms, 1),
                "backends_used": list({r.get("backend", "") for r in results}),
            }
        except Exception as exc:
            return {"ok": False, "hits": 0, "error": str(exc)}

    async def upsert_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Generate real embedding and write to all connected stores + local JSON."""
        try:
            vector = self._embedder.embed_text(text, is_query=False)
        except Exception as exc:
            logger.error("Skipping upsert for %s — embedding failed: %s", doc_id, exc)
            return False

        point_id = doc_id or uuid4().hex
        metadata["embedding_fingerprint"] = self.fingerprint
        metadata["embedding_backend"] = self._embedder._backend
        metadata["is_local_fallback"] = self._embedder.is_local_fallback
        metadata["text"] = text

        # Always write to local JSON store (development cache)
        n_file = NORM_DIR / f"{point_id}.json"
        stored_meta = {**metadata, "vector": vector}
        n_file.write_text(json.dumps(stored_meta, indent=2), encoding="utf-8")

        # pgvector dual-write
        if self._pg_pool is not None:
            try:
                async with self._pg_pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        INSERT INTO {self._table_name} (id, embedding, text, metadata, fingerprint)
                        VALUES ($1, $2::vector, $3, $4::jsonb, $5)
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

        # Milvus dual-write
        if self._milvus_client is not None:
            try:
                row = {"id": point_id, "vector": vector}
                # Milvus schema fields — add only scalar metadata
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        row[k] = v
                self._milvus_client.upsert(
                    collection_name=self._table_name,
                    data=[row],
                )
            except Exception as exc:
                logger.warning("Milvus upsert failed for %s: %s", point_id, exc)

        return True

    async def search_similar(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search all connected backends and return RRF-fused results.

        Returns per-result metadata including source_backend.
        """
        vector = self._embedder.embed_text(query, is_query=True)

        pg_results: list[dict[str, Any]] = []
        milvus_results: list[dict[str, Any]] = []
        local_results: list[dict[str, Any]] = []

        # ── pgvector search ──────────────────────────────────────────
        if self._pg_pool is not None:
            pg_results = await self._search_pgvector(vector, top_k * 2, score_threshold)

        # ── Milvus search ────────────────────────────────────────────
        if self._milvus_client is not None:
            milvus_results = await self._search_milvus(vector, top_k * 2, score_threshold)

        # ── Local JSON fallback (always used in dev, supplements production) ──
        if not pg_results and not milvus_results:
            local_results = self._search_local(vector, top_k * 2, score_threshold, query)

        # ── Fuse with RRF ─────────────────────────────────────────────
        if pg_results and milvus_results:
            fused = reciprocal_rank_fusion(pg_results, milvus_results)
        elif pg_results:
            fused = pg_results
        elif milvus_results:
            fused = milvus_results
        else:
            fused = local_results

        return fused[:top_k]

    async def _search_pgvector(
        self, vector: list[float], top_k: int, score_threshold: float
    ) -> list[dict[str, Any]]:
        try:
            async with self._pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT id, text, metadata, 1 - (embedding <=> $1::vector) AS score
                    FROM {self._table_name}
                    WHERE 1 - (embedding <=> $1::vector) >= $2
                    ORDER BY embedding <=> $1::vector ASC
                    LIMIT $3;
                    """,
                    str(vector),
                    score_threshold,
                    top_k,
                )
                results = []
                for row in rows:
                    meta = json.loads(row["metadata"]) if row["metadata"] else {}
                    results.append({
                        "id": str(row["id"]),
                        "score": float(row["score"]),
                        "text": row["text"] or "",
                        "metadata": meta,
                        "backend": "pgvector",
                    })
                return results
        except Exception as exc:
            logger.warning("pgvector search failed: %s", exc)
            return []

    async def _search_milvus(
        self, vector: list[float], top_k: int, score_threshold: float
    ) -> list[dict[str, Any]]:
        try:
            search_results = self._milvus_client.search(
                collection_name=self._table_name,
                data=[vector],
                limit=top_k,
                output_fields=["text", "source_file", "chunk_id", "title", "publisher", "source_url"],
            )
            results = []
            for hit in search_results[0]:
                score = float(hit.get("distance", 0.0))
                if score < score_threshold:
                    continue
                entity = hit.get("entity", {})
                results.append({
                    "id": str(hit.get("id", "")),
                    "score": score,
                    "text": entity.get("text", ""),
                    "metadata": entity,
                    "backend": "milvus",
                })
            return results
        except Exception as exc:
            logger.warning("Milvus search failed: %s", exc)
            return []

    def _search_local(
        self,
        vector: list[float],
        top_k: int,
        score_threshold: float,
        query: str = "",
    ) -> list[dict[str, Any]]:
        """Search local normalized JSON index (LOCAL_DEVELOPMENT_FALLBACK)."""
        query_words = [
            w.lower() for w in query.lower().split()
            if len(w) > 2 and w.lower() not in STOPWORDS
        ]
        matched_symptom_terms = [
            w for w in query_words
            if any(k in w for k in SYMPTOM_KEYWORDS)
        ]

        candidates: list[dict[str, Any]] = []
        for f_path in NORM_DIR.glob("*.json"):
            try:
                meta = json.loads(f_path.read_text(encoding="utf-8"))
                doc_vector = meta.get("vector")
                if not doc_vector or len(doc_vector) != len(vector):
                    continue

                # Cosine similarity
                dot = sum(a * b for a, b in zip(vector, doc_vector))
                norm_a = (sum(a * a for a in vector)) ** 0.5 or 1.0
                norm_b = (sum(b * b for b in doc_vector)) ** 0.5 or 1.0
                sim = dot / (norm_a * norm_b)

                # Symptom-domain relevance boost (+0.35) — smaller than before to avoid over-ranking
                chunk_text_lower = meta.get("text", "").lower()
                source_lower = meta.get("source_file", "").lower()
                if matched_symptom_terms:
                    if any(
                        term in chunk_text_lower or term in source_lower
                        for term in matched_symptom_terms
                    ):
                        sim = min(1.0, sim + 0.35)

                if sim >= score_threshold and meta.get("retrieval_allowed", True):
                    candidates.append({
                        "id": meta.get("chunk_id", f_path.stem),
                        "score": round(sim, 4),
                        "text": meta.get("text", ""),
                        "metadata": {k: v for k, v in meta.items() if k != "vector"},
                        "backend": _BACKEND_LABEL_LOCAL,
                    })
            except Exception as exc:
                logger.debug("Error reading local chunk %s: %s", f_path, exc)

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

    async def close(self) -> None:
        """Close all database connections."""
        if self._pg_pool is not None:
            try:
                await self._pg_pool.close()
            except Exception:
                pass
            self._pg_connected = False

        if self._milvus_client is not None:
            try:
                self._milvus_client.close()
            except Exception:
                pass
            self._milvus_connected = False

        self._is_connected = False
