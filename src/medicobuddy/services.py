"""Runtime services dependency container for MedicoBuddy AI."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from medicobuddy.config import Settings
from medicobuddy.knowledge_graph.client import Neo4jClient
from medicobuddy.retrieval.embeddings import EmbeddingProvider
from medicobuddy.retrieval.vector_store import VectorStoreClient

logger = logging.getLogger(__name__)


@dataclass
class RuntimeServices:
    """Holds initialized clients and state for the application lifespan.

    MCP is optional — its absence never blocks local retrieval.
    """

    settings: Settings
    embedder: EmbeddingProvider
    vector_store: VectorStoreClient
    neo4j: Neo4jClient
    workflow: Any
    git_sha: str
    mcp: Any = None  # Optional — MCP adapter (MCPClientAdapter or None)

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

        if self.mcp is not None:
            try:
                await self.mcp.close()
            except Exception as exc:
                logger.warning("Error closing MCPClientAdapter: %s", exc)
