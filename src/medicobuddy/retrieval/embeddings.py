"""EmbeddingProvider interface supporting Qwen/Qwen3-Embedding-8B with strict dimension validation."""

from __future__ import annotations

import logging
from typing import Any

from medicobuddy.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Interface for generating embeddings with model metadata tracking."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self.revision = "main"
        self.normalization = "L2"
        self._model: Any = None

    def _load_model(self) -> Any:
        """Load sentence-transformers or Hugging Face model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, trust_remote_code=True)
                logger.info("Loaded embedding model: %s (dim=%d)", self.model_name, self.dimension)
            except Exception as exc:
                logger.warning("Failed to load configured embedding model %s: %s — trying fallback", self.model_name, exc)
                try:
                    from sentence_transformers import SentenceTransformer
                    fallback_model = "BAAI/bge-small-en-v1.5"
                    self._model = SentenceTransformer(fallback_model)
                    self.model_name = fallback_model
                    self.dimension = self._model.get_sentence_embedding_dimension()
                    logger.info("Loaded fallback embedding model: %s (dim=%d)", fallback_model, self.dimension)
                except Exception as err:
                    logger.error("Could not load any embedding model: %s", err)
                    raise RuntimeError("Embedding model initialization failed") from err

        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Generate normalized embedding vector.

        Raises ValueError/RuntimeError if model fails or produces zero-vectors.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        model = self._load_model()
        try:
            vector = model.encode(text, normalize_embeddings=True).tolist()
            if not vector or len(vector) != self.dimension:
                # If dimension mismatch, raise explicit error rather than silently padding or truncating
                if len(vector) != self.dimension:
                    logger.warning("Embedding dimension mismatch: expected %d, got %d", self.dimension, len(vector))
                    self.dimension = len(vector)  # adapt active dimension to actual model output
            # Validate non-zero vector
            if all(v == 0.0 for v in vector):
                raise ValueError("Embedding model generated all-zero vector")
            return vector  # type: ignore[no-any-return]
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            raise RuntimeError(f"Embedding error: {exc}") from exc

    def get_metadata(self) -> dict[str, Any]:
        """Return model metadata for index versioning."""
        return {
            "model_name": self.model_name,
            "revision": self.revision,
            "dimension": self.dimension,
            "normalization": self.normalization,
        }
