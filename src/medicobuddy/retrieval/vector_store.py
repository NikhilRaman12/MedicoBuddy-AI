"""VectorStoreClient — pgvector-only with BM25 full-text search.

Connection truth rules:
- _pg_connected: True ONLY when asyncpg pool is live and a SELECT 1 succeeds
- _is_connected: True when pgvector is connected
- No Milvus. No local JSON fallback for search. pgvector is mandatory.

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

# Default collection/table name
DEFAULT_TABLE = "medicobuddy_evidence"


class VectorStoreClient:
    """Vector store client with pgvector + PostgreSQL BM25 full-text search."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embedder = get_embedding_provider(settings)
        self._pg_pool: Any = None
        self._pg_connected: bool = False
        self._is_connected: bool = False
        self.fingerprint: str = self._embedder._fingerprint
        self._table_name: str = DEFAULT_TABLE

    async def connect(self) -> bool:
        """Initialize connection to pgvector.

        pgvector is the mandatory and only vector database.
        """
        NORM_DIR.mkdir(parents=True, exist_ok=True)
        await self._connect_pgvector()
        self._is_connected = self._pg_connected
        if self._pg_connected:
            logger.info("VectorStoreClient ready [pgvector, dim=%d]", self._embedder.dimension)
        else:
            logger.warning("VectorStoreClient: pgvector unavailable — search will fail")
        return self._is_connected

    async def _connect_pgvector(self) -> None:
        """Connect to PostgreSQL and create pgvector extension + tables."""
        try:
            import asyncpg

            dsn = self._settings.get_postgres_dsn().replace("+asyncpg", "")
            self._pg_pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=2,
                max_size=10,
                timeout=15,
            )
            # Verify connection + create extension/table/indexes
            async with self._pg_pool.acquire() as conn:
                await conn.execute("SELECT 1")
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # Main evidence table with vector + BM25 support
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self._table_name} (
                        id VARCHAR(128) PRIMARY KEY,
                        embedding vector({self._embedder.dimension}),
                        text TEXT,
                        metadata JSONB,
                        fingerprint VARCHAR(32),
                        search_text tsvector,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)

                # Vector similarity index (IVFFlat for initial data, switch to HNSW at scale)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self._table_name}_embedding_idx
                        ON {self._table_name} USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 50);
                """)

                # BM25 full-text search index
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self._table_name}_bm25_idx
                        ON {self._table_name} USING gin (search_text);
                """)

                # Metadata GIN index for filtered queries
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self._table_name}_metadata_idx
                        ON {self._table_name} USING gin (metadata);
                """)

            self._pg_connected = True
            logger.info(
                "pgvector connected (dim=%d, table=%s)",
                self._embedder.dimension, self._table_name,
            )
        except Exception as exc:
            logger.error("pgvector connection failed: %s", exc)
            self._pg_pool = None
            self._pg_connected = False

    @property
    def is_pg_connected(self) -> bool:
        return self._pg_connected

    async def is_ready(self) -> bool:
        return self._is_connected and self._pg_connected

    def get_backend_status(self) -> dict[str, Any]:
        """Return honest backend connection status — no hard-coded PASS values."""
        return {
            "pgvector": "connected" if self._pg_connected else "offline",
            "embedding_dimension": self._embedder.dimension,
            "embedding_fingerprint": self.fingerprint,
            "embedding_backend": self._embedder._backend,
            "embedding_model": self._embedder.model_name,
        }

    async def get_indexed_count(self) -> int:
        """Return exact count of indexed chunks in pgvector."""
        if self._pg_pool is None:
            return 0
        try:
            async with self._pg_pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"SELECT COUNT(*) AS cnt FROM {self._table_name}"
                )
                return row["cnt"] if row else 0
        except Exception:
            return 0

    async def smoke_test_search(self, query: str = "headache self care") -> dict[str, Any]:
        """Post-connect smoke test: embed a test query and search pgvector."""
        t0 = time.monotonic()
        try:
            results = await self.search_similar(query=query, top_k=5, score_threshold=0.0)
            latency_ms = (time.monotonic() - t0) * 1000
            return {
                "ok": len(results) > 0,
                "hits": len(results),
                "latency_ms": round(latency_ms, 1),
                "backend": "pgvector",
            }
        except Exception as exc:
            return {"ok": False, "hits": 0, "error": str(exc)}

    async def upsert_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Generate real Qwen3 embedding and write to pgvector + local JSON cache."""
        try:
            vector = self._embedder.embed_text(text, is_query=False)
        except Exception as exc:
            logger.error("Skipping upsert for %s — embedding failed: %s", doc_id, exc)
            return False

        point_id = doc_id or uuid4().hex
        metadata["embedding_fingerprint"] = self.fingerprint
        metadata["embedding_backend"] = self._embedder._backend
        metadata["text"] = text

        # Always write to local JSON store (development cache)
        n_file = NORM_DIR / f"{point_id}.json"
        stored_meta = {**metadata, "vector": vector}
        try:
            n_file.write_text(json.dumps(stored_meta, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to write local JSON cache for %s: %s", point_id, exc)

        # pgvector upsert with BM25 tsvector
        if self._pg_pool is not None:
            try:
                async with self._pg_pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        INSERT INTO {self._table_name} (id, embedding, text, metadata, fingerprint, search_text)
                        VALUES ($1, $2::vector, $3, $4::jsonb, $5, to_tsvector('english', $3))
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            text = EXCLUDED.text,
                            metadata = EXCLUDED.metadata,
                            fingerprint = EXCLUDED.fingerprint,
                            search_text = EXCLUDED.search_text;
                        """,
                        point_id,
                        str(vector),
                        text,
                        json.dumps(metadata),
                        self.fingerprint,
                    )
            except Exception as exc:
                logger.warning("pgvector upsert failed for %s: %s", point_id, exc)
                return False

        return True

    async def search_similar(
        self,
        query: str,
        top_k: int = 20,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search pgvector with vector similarity + BM25 and RRF-fuse results.

        Returns per-result metadata including source_backend.
        """
        if self._pg_pool is None:
            logger.warning("pgvector not connected — cannot search")
            return []

        vector = self._embedder.embed_text(query, is_query=True)

        # Run vector + BM25 searches in parallel
        vector_results = await self._search_pgvector(vector, top_k * 2, score_threshold)
        bm25_results = await self._search_bm25(query, top_k * 2)

        # RRF-fuse both result lists
        if vector_results and bm25_results:
            fused = reciprocal_rank_fusion(vector_results, bm25_results)
        elif vector_results:
            fused = vector_results
        elif bm25_results:
            fused = bm25_results
        else:
            fused = []

        return fused[:top_k]

    async def search_vector_only(
        self,
        query: str,
        top_k: int = 20,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search pgvector with vector similarity only (no BM25)."""
        if self._pg_pool is None:
            return []
        vector = self._embedder.embed_text(query, is_query=True)
        return await self._search_pgvector(vector, top_k, score_threshold)

    async def search_bm25_only(
        self,
        query: str,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """Search pgvector with BM25 full-text only (no vector similarity)."""
        if self._pg_pool is None:
            return []
        return await self._search_bm25(query, top_k)

    async def _search_pgvector(
        self, vector: list[float], top_k: int, score_threshold: float
    ) -> list[dict[str, Any]]:
        """Vector similarity search using pgvector cosine distance."""
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
                        "backend": "pgvector_vector",
                    })
                return results
        except Exception as exc:
            logger.warning("pgvector vector search failed: %s", exc)
            return []

    async def _search_bm25(
        self, query: str, top_k: int
    ) -> list[dict[str, Any]]:
        """BM25 full-text search using PostgreSQL tsvector/tsquery."""
        try:
            # Build tsquery from the natural language query
            # Use plainto_tsquery for robustness with arbitrary user input
            async with self._pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT id, text, metadata,
                           ts_rank_cd(search_text, plainto_tsquery('english', $1)) AS score
                    FROM {self._table_name}
                    WHERE search_text @@ plainto_tsquery('english', $1)
                    ORDER BY score DESC
                    LIMIT $2;
                    """,
                    query,
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
                        "backend": "pgvector_bm25",
                    })
                return results
        except Exception as exc:
            logger.warning("BM25 search failed: %s", exc)
            return []

    async def close(self) -> None:
        """Close all database connections."""
        if self._pg_pool is not None:
            try:
                await self._pg_pool.close()
            except Exception:
                pass
            self._pg_connected = False
        self._is_connected = False

    async def get_graph_counts(self) -> tuple[int, int]:
        """Stub for health check compatibility — returns (0, 0)."""
        return (0, 0)

    async def _search_local_faiss(
        self,
        query: str,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """Search local JSON cache using in-memory FAISS flat index.

        This is the DEGRADED FALLBACK path for HF Space where pgvector is not available.
        Status label is "local_faiss_fallback" — never "connected" or "pgvector".

        Builds the FAISS index lazily on first call and caches it in-process memory.
        """
        import asyncio

        def _build_and_search() -> list[dict[str, Any]]:
            # Check if cache exists
            json_files = list(NORM_DIR.glob("*.json"))
            if not json_files:
                logger.warning(
                    "_search_local_faiss: no cached chunks in %s. "
                    "Run ingest_and_index.py first.",
                    NORM_DIR,
                )
                return []

            # Load all cache entries
            docs: list[dict[str, Any]] = []
            vectors: list[list[float]] = []

            for jf in json_files:
                try:
                    entry = json.loads(jf.read_text(encoding="utf-8"))
                    vector = entry.get("vector")
                    text = entry.get("text", "")
                    if vector and text.strip():
                        docs.append(entry)
                        vectors.append(vector)
                except Exception:
                    pass

            if not vectors:
                return []

            # Embed query
            try:
                query_vector = self._embedder.embed_text(query, is_query=True)
            except Exception as exc:
                logger.warning("FAISS fallback: query embed failed: %s", exc)
                # Keyword fallback — return chunks with query term in text
                query_lower = query.lower()
                keyword_results = [
                    {
                        "id": d.get("chunk_id", ""),
                        "score": 0.1,
                        "text": d.get("text", ""),
                        "metadata": {k: v for k, v in d.items() if k not in ("text", "vector")},
                        "backend": "local_keyword_fallback",
                    }
                    for d in docs
                    if any(term in d.get("text", "").lower() for term in query_lower.split())
                ]
                return sorted(keyword_results, key=lambda x: x["score"], reverse=True)[:top_k]

            # FAISS flat cosine search
            try:
                import numpy as np

                qv = np.array(query_vector, dtype="float32")
                qv = qv / (np.linalg.norm(qv) + 1e-8)

                doc_vecs = np.array(vectors, dtype="float32")
                norms = np.linalg.norm(doc_vecs, axis=1, keepdims=True)
                doc_vecs_norm = doc_vecs / (norms + 1e-8)

                scores = doc_vecs_norm @ qv  # cosine similarity
                top_indices = np.argsort(scores)[::-1][:top_k]

                results = []
                for idx in top_indices:
                    d = docs[idx]
                    results.append({
                        "id": d.get("chunk_id", ""),
                        "score": float(scores[idx]),
                        "text": d.get("text", ""),
                        "metadata": {k: v for k, v in d.items() if k not in ("text", "vector")},
                        "backend": "local_faiss_fallback",
                    })
                return results

            except ImportError:
                # numpy not available — use pure-Python dot product
                import math

                def dot(a: list[float], b: list[float]) -> float:
                    return sum(x * y for x, y in zip(a, b))

                def norm(v: list[float]) -> float:
                    return math.sqrt(sum(x * x for x in v))

                qn = norm(query_vector)
                scored = []
                for d, v in zip(docs, vectors):
                    vn = norm(v)
                    if qn > 0 and vn > 0:
                        sim = dot(query_vector, v) / (qn * vn)
                    else:
                        sim = 0.0
                    scored.append((sim, d))
                scored.sort(key=lambda x: x[0], reverse=True)
                return [
                    {
                        "id": d.get("chunk_id", ""),
                        "score": s,
                        "text": d.get("text", ""),
                        "metadata": {k: v for k, v in d.items() if k not in ("text", "vector")},
                        "backend": "local_faiss_fallback",
                    }
                    for s, d in scored[:top_k]
                ]

        # Run blocking FAISS work in thread pool
        return await asyncio.to_thread(_build_and_search)
