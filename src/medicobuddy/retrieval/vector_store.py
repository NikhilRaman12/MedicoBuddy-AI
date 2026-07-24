"""Vector store client supporting Milvus (Primary) and PostgreSQL pgvector with Qwen3-Embedding-8B."""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from medicobuddy.config import Settings

logger = logging.getLogger(__name__)


class VectorStoreClient:
    """Milvus & pgvector vector store client with Qwen3-Embedding-8B embeddings."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._milvus_client: Any = None
        self._pg_pool: Any = None
        self._embedding_model: Any = None
        self._dimension = settings.embedding_dimension

    async def connect(self) -> None:
        """Initialize Milvus client and pgvector connection."""
        # 1. Connect Milvus (Primary Vector DB)
        try:
            from pymilvus import MilvusClient

            self._milvus_client = MilvusClient(
                uri=f"http://{self._settings.milvus_host}:{self._settings.milvus_port}"
            )
            # Create collection if not exists
            if not self._milvus_client.has_collection(self._settings.milvus_collection):
                self._milvus_client.create_collection(
                    collection_name=self._settings.milvus_collection,
                    dimension=self._dimension,
                    metric_type="COSINE",
                    auto_id=False,
                    id_type="string",
                    max_length=64,
                )
                logger.info("Created Milvus collection: %s", self._settings.milvus_collection)
            logger.info("Connected to Milvus at %s:%d", self._settings.milvus_host, self._settings.milvus_port)
        except Exception:
            logger.warning("Milvus primary vector DB unavailable — falling back to Qdrant/pgvector", exc_info=True)
            self._milvus_client = None

        # 2. Connect pgvector (Secondary Vector DB)
        if self._settings.enable_pgvector:
            try:
                import asyncpg
                self._pg_pool = await asyncpg.create_pool(
                    dsn=self._settings.postgres_dsn.replace("+asyncpg", ""),
                    min_size=1,
                    max_size=5,
                )
                async with self._pg_pool.acquire() as conn:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    await conn.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self._settings.milvus_collection} (
                            id VARCHAR(64) PRIMARY KEY,
                            embedding vector({self._dimension}),
                            text TEXT,
                            metadata JSONB
                        );
                        """
                    )
                logger.info("Connected to PostgreSQL pgvector")
            except Exception:
                logger.warning("PostgreSQL pgvector unavailable", exc_info=True)
                self._pg_pool = None

    def _get_embedding_model(self) -> Any:
        """Load Qwen3-Embedding-8B / sentence-transformers embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(
                    self._settings.embedding_model,
                    trust_remote_code=True,
                )
                logger.info("Loaded embedding model: %s", self._settings.embedding_model)
            except Exception:
                # Fallback to standard biomedical embedding model if 8B checkpoint requires specific device
                try:
                    from sentence_transformers import SentenceTransformer
                    fallback_model = "BAAI/bge-large-en-v1.5"
                    self._embedding_model = SentenceTransformer(fallback_model)
                    logger.info("Loaded fallback embedding model: %s", fallback_model)
                except Exception:
                    logger.warning("Embedding model failed to load", exc_info=True)
        return self._embedding_model

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector using Qwen3-Embedding-8B."""
        model = self._get_embedding_model()
        if model is None:
            return [0.0] * self._dimension
        try:
            embedding = model.encode(text, normalize_embeddings=True)
            vec = embedding.tolist()  # type: ignore[no-any-return]
            if len(vec) != self._dimension:
                # Truncate or pad to match configured dimension if model produces different dim
                if len(vec) > self._dimension:
                    vec = vec[: self._dimension]
                else:
                    vec = vec + [0.0] * (self._dimension - len(vec))
            return vec
        except Exception:
            logger.error("Embedding generation failed", exc_info=True)
            return [0.0] * self._dimension

    async def upsert_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        """Insert or update a document in Milvus and pgvector."""
        vector = self.embed_text(text)
        point_id = doc_id or uuid4().hex

        # Upsert into Milvus
        if self._milvus_client is not None:
            try:
                data = [{"id": point_id, "vector": vector, "text": text, **metadata}]
                self._milvus_client.upsert(
                    collection_name=self._settings.milvus_collection,
                    data=data,
                )
            except Exception:
                logger.warning("Milvus upsert failed", exc_info=True)

        # Upsert into pgvector
        if self._pg_pool is not None:
            try:
                import json
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
            except Exception:
                logger.warning("pgvector upsert failed", exc_info=True)

    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Search similar documents across Milvus or pgvector."""
        vector = self.embed_text(query)
        results: list[dict[str, Any]] = []

        # 1. Search Milvus (Primary)
        if self._milvus_client is not None:
            try:
                res = self._milvus_client.search(
                    collection_name=self._settings.milvus_collection,
                    data=[vector],
                    limit=top_k,
                    output_fields=["text", "title", "doi", "pmid"],
                )
                for hits in res:
                    for hit in hits:
                        distance = hit.get("distance", 0.0)
                        if distance >= score_threshold:
                            entity = hit.get("entity", {})
                            results.append({
                                "id": str(hit.get("id")),
                                "score": distance,
                                "text": entity.get("text", ""),
                                "metadata": {k: v for k, v in entity.items() if k != "text"},
                            })
                if results:
                    return results
            except Exception:
                logger.warning("Milvus search failed — trying pgvector fallback", exc_info=True)

        # 2. Search pgvector (Fallback)
        if self._pg_pool is not None:
            try:
                import json
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
                        })
                return results
            except Exception:
                logger.warning("pgvector search failed", exc_info=True)

        return results

    async def close(self) -> None:
        """Close database connections."""
        if self._milvus_client is not None:
            try:
                self._milvus_client.close()
            except Exception:
                pass
        if self._pg_pool is not None:
            await self._pg_pool.close()
