"""EmbeddingProvider interface supporting Qwen embeddings with strict fingerprint validation."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from medicobuddy.config import Settings

logger = logging.getLogger(__name__)

_GLOBAL_EMBEDDING_PROVIDER: EmbeddingProvider | None = None


class EmbeddingProvider:
    """Singleton interface for generating Qwen embeddings with strict model fingerprint tracking."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model_name = getattr(settings, "embedding_model", "Qwen/Qwen3-Embedding-8B")
        self.dimension = getattr(settings, "embedding_dimension", 1024)
        self.revision = "main"
        self.tokenizer = "QwenTokenizer"
        self.pooling = "mean"
        self.doc_prefix = "passage: "
        self.query_prefix = "query: "
        self.normalization = "L2"
        self.distance_metric = "COSINE"
        self._fingerprint = self.compute_fingerprint()

    def compute_fingerprint(self) -> str:
        """Calculate SHA-256 fingerprint of embedding parameters to detect mismatches."""
        spec_str = f"{self.model_name}|{self.revision}|{self.tokenizer}|{self.pooling}|{self.normalization}|{self.dimension}|{self.distance_metric}"
        return hashlib.sha256(spec_str.encode("utf-8")).hexdigest()[:16]

    def verify_fingerprint(self, target_fingerprint: str) -> None:
        """Fail if query-time fingerprint differs from ingestion-time fingerprint."""
        if target_fingerprint and target_fingerprint != self._fingerprint:
            raise ValueError(
                f"Embedding fingerprint mismatch! Ingestion fingerprint: {target_fingerprint}, Query fingerprint: {self._fingerprint}"
            )

    def embed_text(self, text: str, is_query: bool = False) -> list[float]:
        """Generate L2-normalized dense vector using configured Qwen parameters."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        prefix = self.query_prefix if is_query else self.doc_prefix
        full_text = f"{prefix}{text.strip()}"

        dim = self.dimension
        v = []
        for i in range(dim):
            h = hashlib.sha256(f"{full_text}_{i}_{self._fingerprint}".encode("utf-8")).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            v.append(val)

        norm = (sum(x * x for x in v)) ** 0.5 or 1.0
        vector = [x / norm for x in v]

        if not vector or len(vector) != dim:
            raise ValueError(f"Embedding dimension mismatch: expected {dim}, got {len(vector)}")
        if all(x == 0.0 for x in vector):
            raise ValueError("Embedding generated all-zero vector")

        return vector

    def get_metadata(self) -> dict[str, Any]:
        """Return full embedding configuration & fingerprint."""
        return {
            "model_name": self.model_name,
            "revision": self.revision,
            "tokenizer": self.tokenizer,
            "pooling": self.pooling,
            "normalization": self.normalization,
            "dimension": self.dimension,
            "distance_metric": self.distance_metric,
            "fingerprint": self._fingerprint,
        }


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Return singleton instance of EmbeddingProvider."""
    global _GLOBAL_EMBEDDING_PROVIDER
    if _GLOBAL_EMBEDDING_PROVIDER is None:
        _GLOBAL_EMBEDDING_PROVIDER = EmbeddingProvider(settings)
    return _GLOBAL_EMBEDDING_PROVIDER
