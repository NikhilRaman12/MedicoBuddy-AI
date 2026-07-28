"""Runtime services dependency container for MedicoBuddy AI."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from medicobuddy.config import Settings
from medicobuddy.knowledge_graph.client import Neo4jClient
from medicobuddy.mcp.client import MCPClientAdapter
from medicobuddy.retrieval.embeddings import EmbeddingProvider
from medicobuddy.retrieval.vector_store import VectorStoreClient

logger = logging.getLogger(__name__)


@dataclass
class RuntimeServices:
    """Holds initialized clients and state for the application lifespan."""

    settings: Settings
    embedder: EmbeddingProvider
    vector_store: VectorStoreClient
    neo4j: Neo4jClient
    mcp: MCPClientAdapter
    workflow: Any
    git_sha: str

    async def close_all(self) -> None:
        """Close all active connections."""
        try:
            await self.vector_store.close()
        except Exception as exc:
            logger.warning("Error closing VectorStoreClient: %s", exc)

        try:
            await self.neo4j.close()
        except Exception as exc:
            logger.warning("Error closing Neo4jClient: %s", exc)

        try:
            await self.mcp.close()
        except Exception as exc:
            logger.warning("Error closing MCPClientAdapter: %s", exc)
