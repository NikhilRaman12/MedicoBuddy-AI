"""Qwen3-Embedding-0.6B embedding provider for MedicoBuddy AI.

Production path: Qwen/Qwen3-Embedding-0.6B loaded locally via sentence-transformers.
Dimension: 1024, L2-normalized, cosine distance.

No remote endpoints, no HF tokens, no MiniLM fallback, no hash vectors.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from medicobuddy.config import Settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_MANIFEST_PATH = PROJECT_ROOT / "evidence" / "index_manifest.json"


class EmbeddingFingerprintMismatch(ValueError):
    """Raised when query-time embedding fingerprint differs from ingestion-time fingerprint."""


class EmbeddingProvider:
    """Embedding provider using Qwen/Qwen3-Embedding-0.6B locally.

    Produces real 1024-dimensional L2-normalized dense vectors.
    No fallback to MiniLM, hash vectors, random embeddings, or mock embeddings.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._backend: str = "uninitialized"
        self._model: Any = None

        self.model_name: str = settings.embedding_model
        self.dimension: int = settings.embedding_dimension or 1024
        self.revision: str = "main"
        self.pooling: str = "mean"
        self.normalization: str = "L2"
        self.distance_metric: str = "COSINE"
        self._fingerprint: str = ""
        self.is_local_fallback: bool = False  # This IS the production model

        self._initialize()

    def _initialize(self) -> None:
        """Load Qwen/Qwen3-Embedding-0.6B via sentence-transformers."""
        model_name = self._settings.embedding_model or "Qwen/Qwen3-Embedding-0.6B"

        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading Qwen3 embedding model: %s", model_name)
            self._model = SentenceTransformer(model_name, trust_remote_code=True)
            self.model_name = model_name
            actual_dim = self._model.get_sentence_embedding_dimension()
            if actual_dim:
                self.dimension = actual_dim
            self._backend = "qwen3_local"
            self.is_local_fallback = False
            logger.info(
                "Qwen3 embedding model loaded: %s (dim=%d, backend=%s)",
                model_name, self.dimension, self._backend,
            )
        except Exception as exc:
            logger.error(
                "FATAL: Failed to load Qwen3 embedding model '%s': %s. "
                "Ensure sentence-transformers and torch are installed. "
                "Do NOT substitute with MiniLM, hash vectors, or mock embeddings.",
                model_name, exc,
            )
            self._backend = "ERROR"
            self.model_name = model_name
            self.dimension = 1024
            self.is_local_fallback = False

        self._fingerprint = self._compute_fingerprint()
        self._write_index_manifest()

    def embed_text(self, text: str, is_query: bool = False) -> list[float]:
        """Generate a real L2-normalized 1024-dim Qwen3 embedding vector for text."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        if self._backend == "ERROR":
            raise RuntimeError(
                "Qwen3 embedding model failed to initialize. "
                "Install sentence-transformers and torch. "
                "Do NOT substitute with MiniLM, hash vectors, or mock embeddings."
            )

        cleaned_text = text.strip()
        embedding = self._model.encode(cleaned_text, normalize_embeddings=True)
        vector = embedding.tolist()

        if len(vector) != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {len(vector)}"
            )
        if all(x == 0.0 for x in vector):
            raise ValueError("Embedding returned all-zero vector")

        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if self._backend == "ERROR":
            raise RuntimeError("Qwen3 embedding model failed to initialize.")

        cleaned = [t.strip() for t in texts if t and t.strip()]
        if not cleaned:
            return []

        embeddings = self._model.encode(cleaned, normalize_embeddings=True, batch_size=32)
        return [e.tolist() for e in embeddings]

    def _compute_fingerprint(self) -> str:
        """Compute a stable fingerprint from model spec for ingestion/query consistency check."""
        spec_str = (
            f"{self.model_name}|{self.revision}|{self.pooling}|"
            f"{self.normalization}|{self.dimension}|{self.distance_metric}"
        )
        return hashlib.sha256(spec_str.encode("utf-8")).hexdigest()[:16]

    def verify_fingerprint(self, target_fingerprint: str) -> None:
        """Raise EmbeddingFingerprintMismatch when fingerprints differ."""
        if target_fingerprint and target_fingerprint != self._fingerprint:
            raise EmbeddingFingerprintMismatch(
                f"EMBEDDING_FINGERPRINT_MISMATCH: "
                f"ingestion={target_fingerprint}, query={self._fingerprint}. "
                f"Re-run ingestion with the current embedding model to fix."
            )

    def _write_index_manifest(self) -> None:
        """Persist model spec + fingerprint to evidence/index_manifest.json."""
        try:
            INDEX_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
            manifest = {
                "model_name": self.model_name,
                "revision": self.revision,
                "dimension": self.dimension,
                "pooling": self.pooling,
                "normalization": self.normalization,
                "distance_metric": self.distance_metric,
                "fingerprint": self._fingerprint,
                "backend": self._backend,
                "is_local_fallback": self.is_local_fallback,
                "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            INDEX_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            logger.info("Index manifest written to %s", INDEX_MANIFEST_PATH)
        except Exception as exc:
            logger.warning("Failed to write index manifest: %s", exc)

    def get_metadata(self) -> dict[str, Any]:
        """Return full embedding configuration & fingerprint."""
        return {
            "model_name": self.model_name,
            "revision": self.revision,
            "dimension": self.dimension,
            "pooling": self.pooling,
            "normalization": self.normalization,
            "distance_metric": self.distance_metric,
            "fingerprint": self._fingerprint,
            "backend": self._backend,
            "is_local_fallback": self.is_local_fallback,
        }


_GLOBAL_EMBEDDING_PROVIDER: EmbeddingProvider | None = None


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Return singleton EmbeddingProvider instance."""
    global _GLOBAL_EMBEDDING_PROVIDER
    if _GLOBAL_EMBEDDING_PROVIDER is None:
        _GLOBAL_EMBEDDING_PROVIDER = EmbeddingProvider(settings)
    return _GLOBAL_EMBEDDING_PROVIDER


def reset_embedding_provider() -> None:
    """Reset singleton (for testing)."""
    global _GLOBAL_EMBEDDING_PROVIDER
    _GLOBAL_EMBEDDING_PROVIDER = None
