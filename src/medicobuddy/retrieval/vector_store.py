"""VectorStoreRouter supporting Milvus (Primary) and PostgreSQL pgvector (Failover)."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from medicobuddy.config import Settings
from medicobuddy.retrieval.embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


class VectorStoreClient:
    """Milvus & pgvector vector store client with EmbeddingProvider integration."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embedder = EmbeddingProvider(settings)
        self._milvus_client: Any = None
        self._pg_pool: Any = None
        self._is_connected = False

    async def connect(self) -> bool:
        """Initialize connections to Milvus and pgvector."""
        # 1. Connect Milvus Primary
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
                logger.info("Created Milvus collection: %s", self._settings.milvus_collection)
            logger.info("Connected to Milvus primary at %s", milvus_uri)
            self._is_connected = True
        except Exception as exc:
            logger.warning("Milvus primary vector DB unavailable (%s) — using pgvector failover", exc)
            self._milvus_client = None

        # 2. Connect pgvector Secondary
        if self._settings.enable_pgvector:
            try:
                import asyncpg
                dsn = self._settings.postgres_dsn.replace("+asyncpg", "")
                self._pg_pool = await asyncpg.create_pool(
                    dsn=dsn,
                    min_size=1,
                    max_size=5,
                )
                async with self._pg_pool.acquire() as conn:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    await conn.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self._settings.milvus_collection} (
                            id VARCHAR(64) PRIMARY KEY,
                            embedding vector({self._embedder.dimension}),
                            text TEXT,
                            metadata JSONB
                        );
                        """
                    )
                logger.info("Connected to PostgreSQL pgvector secondary")
                self._is_connected = True
            except Exception as exc:
                logger.warning("PostgreSQL pgvector secondary unavailable: %s", exc)
                self._pg_pool = None

        return self._is_connected

    async def is_ready(self) -> bool:
        """Check if vector store is connected and operational."""
        return self._is_connected and (self._milvus_client is not None or self._pg_pool is not None)

    async def upsert_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Dual-write document embeddings into Milvus primary and pgvector failover."""
        try:
            vector = self._embedder.embed_text(text)
        except Exception as exc:
            logger.error("Skipping upsert for %s — embedding failed: %s", doc_id, exc)
            return False

        point_id = doc_id or uuid4().hex
        success = False

        # Milvus Primary
        if self._milvus_client is not None:
            try:
                data = [{"id": point_id, "vector": vector, "text": text, **metadata}]
                self._milvus_client.upsert(
                    collection_name=self._settings.milvus_collection,
                    data=data,
                )
                success = True
            except Exception as exc:
                logger.warning("Milvus upsert failed for %s: %s", point_id, exc)

        # pgvector Secondary
        if self._pg_pool is not None:
            try:
                async with self._pg_pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        INSERT INTO {self._settings.milvus_collection} (id, embedding, text, metadata)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            text = EXCLUDED.text,
                            metadata = EXCLUDED.metadata;
                        """,
                        point_id,
                        str(vector),
                        text,
                        json.dumps(metadata),
                    )
                success = True
            except Exception as exc:
                logger.warning("pgvector upsert failed for %s: %s", point_id, exc)

        return success

    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.25,
    ) -> list[dict[str, Any]]:
        """Search Milvus primary first, failing over to pgvector if needed."""
        try:
            vector = self._embedder.embed_text(query)
        except Exception as exc:
            logger.warning("Vector search skipped — embedding failed: %s", exc)
            return []

        results: list[dict[str, Any]] = []

        # 1. Milvus Primary
        if self._milvus_client is not None:
            try:
                res = self._milvus_client.search(
                    collection_name=self._settings.milvus_collection,
                    data=[vector],
                    limit=top_k,
                    output_fields=["text", "publisher", "source_url", "study_type"],
                )
                for hits in res:
                    for hit in hits:
                        dist = hit.get("distance", 0.0)
                        if dist >= score_threshold:
                            entity = hit.get("entity", {})
                            results.append({
                                "id": str(hit.get("id")),
                                "score": float(dist),
                                "text": entity.get("text", ""),
                                "metadata": {k: v for k, v in entity.items() if k != "text"},
                                "backend": "milvus",
                            })
                if results:
                    return results
            except Exception as exc:
                logger.warning("Milvus search failed (%s) — falling back to pgvector", exc)

        # 2. pgvector Failover
        if self._pg_pool is not None:
            try:
                async with self._pg_pool.acquire() as conn:
                    rows = await conn.fetch(
                        f"""
                        SELECT id, text, metadata, 1 - (embedding <=> $1) AS score
                        FROM {self._settings.milvus_collection}
                        WHERE 1 - (embedding <=> $1) >= $2
                        ORDER BY embedding <=> $1 ASC
                        LIMIT $3;
                        """,
                        str(vector),
                        score_threshold,
                        top_k,
                    )
                    for row in rows:
                        results.append({
                            "id": str(row["id"]),
                            "score": float(row["score"]),
                            "text": row["text"] or "",
                            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                            "backend": "pgvector",
                        })
                return results
            except Exception as exc:
                logger.warning("pgvector search failed: %s", exc)

        return results

    async def close(self) -> None:
        """Close database connection clients."""
        if self._milvus_client is not None:
            try:
                self._milvus_client.close()
            except Exception:
                pass
        if self._pg_pool is not None:
            try:
                await self._pg_pool.close()
            except Exception:
                pass
        self._is_connected = False
