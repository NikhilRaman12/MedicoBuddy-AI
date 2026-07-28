"""Real embedding provider for MedicoBuddy AI.

Production path: Qwen/Qwen3-Embedding-8B via HuggingFace Inference Endpoint
  (set QWEN_EMBEDDING_ENDPOINT + HF_TOKEN environment variables).

Development fallback: sentence-transformers/all-MiniLM-L6-v2 loaded locally.
  Clearly labelled LOCAL_DEVELOPMENT_FALLBACK in all result metadata.

The SHA-256 pseudo-embedding implementation has been DELETED.
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
    """Embedding provider with strict fingerprint tracking.

    Uses one of:
    1. HuggingFace Inference Endpoint (QWEN_EMBEDDING_ENDPOINT set) — production
    2. Local sentence-transformers (fallback) — LOCAL_DEVELOPMENT_FALLBACK
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._backend: str = "uninitialized"
        self._model: Any = None
        self._tokenizer: Any = None

        self.model_name: str = settings.embedding_model
        self.dimension: int = settings.embedding_dimension or 0
        self.revision: str = "main"
        self.pooling: str = "mean"
        self.normalization: str = "L2"
        self.distance_metric: str = "COSINE"
        self._fingerprint: str = ""
        self.is_local_fallback: bool = False

        self._initialize()

    def _initialize(self) -> None:
        """Initialize embedding backend — try HF endpoint, then local model."""
        endpoint = self._settings.qwen_embedding_endpoint.strip()
        hf_token = self._settings.hf_token.strip()

        if endpoint:
            logger.info("Initializing Qwen embedding via HF Inference Endpoint: %s", endpoint)
            self._backend = "hf_endpoint"
            self.is_local_fallback = False
            # Probe the endpoint to get real dimension
            try:
                test_vec = self._embed_via_endpoint("health check", endpoint, hf_token)
                self.dimension = len(test_vec)
                logger.info("Qwen HF Endpoint online, dimension=%d", self.dimension)
            except Exception as exc:
                logger.warning("Qwen HF Endpoint probe failed (%s) — falling back to local model", exc)
                self._init_local_fallback()
        else:
            logger.info("QWEN_EMBEDDING_ENDPOINT not set — using local sentence-transformers (LOCAL_DEVELOPMENT_FALLBACK)")
            self._init_local_fallback()

        self._fingerprint = self._compute_fingerprint()
        self._write_index_manifest()

    def _init_local_fallback(self) -> None:
        """Load a real local embedding model as LOCAL_DEVELOPMENT_FALLBACK."""
        try:
            from sentence_transformers import SentenceTransformer
            fallback_model = "sentence-transformers/all-MiniLM-L6-v2"
            logger.info("Loading local embedding model: %s", fallback_model)
            self._model = SentenceTransformer(fallback_model)
            self.model_name = fallback_model
            self.dimension = self._model.get_sentence_embedding_dimension()
            self._backend = "LOCAL_DEVELOPMENT_FALLBACK"
            self.is_local_fallback = True
            logger.info(
                "LOCAL_DEVELOPMENT_FALLBACK embedding ready: %s (dim=%d). "
                "Set QWEN_EMBEDDING_ENDPOINT for production Qwen embeddings.",
                fallback_model, self.dimension,
            )
        except ImportError:
            logger.error(
                "sentence-transformers not installed. Install with: pip install sentence-transformers. "
                "Setting backend to ERROR."
            )
            self._backend = "ERROR"
            self.model_name = "unavailable"
            self.dimension = 384
            self.is_local_fallback = True

    def _embed_via_endpoint(self, text: str, endpoint: str, token: str) -> list[float]:
        """Call HuggingFace TEI or Inference Endpoint for a single text embedding."""
        import httpx

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {"inputs": text}
        timeout = self._settings.embedding_timeout_seconds

        resp = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        # HF TEI returns [[float...]] or [float...]
        if isinstance(data, list):
            if data and isinstance(data[0], list):
                return [float(x) for x in data[0]]
            return [float(x) for x in data]
        raise ValueError(f"Unexpected embedding response format: {type(data)}")

    def embed_text(self, text: str, is_query: bool = False) -> list[float]:
        """Generate a real L2-normalized dense embedding vector for text."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        if self._backend == "ERROR":
            raise RuntimeError(
                "Embedding backend failed to initialize. "
                "Install sentence-transformers or set QWEN_EMBEDDING_ENDPOINT."
            )

        cleaned_text = text.strip()

        if self._backend == "hf_endpoint":
            endpoint = self._settings.qwen_embedding_endpoint.strip()
            token = self._settings.hf_token.strip()
            vector = self._embed_via_endpoint(cleaned_text, endpoint, token)
        elif self._backend == "LOCAL_DEVELOPMENT_FALLBACK":
            embedding = self._model.encode(cleaned_text, normalize_embeddings=True)
            vector = embedding.tolist()
        else:
            raise RuntimeError(f"Unknown embedding backend: {self._backend}")

        if len(vector) != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {len(vector)}"
            )
        if all(x == 0.0 for x in vector):
            raise ValueError("Embedding returned all-zero vector")

        return vector

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
