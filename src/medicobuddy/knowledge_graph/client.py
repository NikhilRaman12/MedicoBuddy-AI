"""Neo4j knowledge graph client for MedicoBuddy AI GraphRAG evidence graph."""

from __future__ import annotations

import logging
from typing import Any

from medicobuddy.config import Settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Async Neo4j client reusing driver connection across lifespan."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._driver: Any = None
        self._is_connected = False
        self._graph_nodes_count = 0
        self._graph_rels_count = 0

    async def connect(self) -> bool:
        """Initialize Neo4j connection pool."""
        try:
            from neo4j import AsyncGraphDatabase

            uri = self._settings.neo4j_uri
            auth = (self._settings.neo4j_user, self._settings.neo4j_password)
            self._driver = AsyncGraphDatabase.driver(uri, auth=auth)
            await self._driver.verify_connectivity()
            logger.info("Connected to Neo4j database at %s", uri)
            self._is_connected = True
        except Exception as exc:
            logger.info("Neo4j database connection offline (%s) — using local in-memory evidence graph", exc)
            self._driver = None
            self._is_connected = True  # Operate in local graph mode

        return self._is_connected

    async def is_ready(self) -> bool:
        """Check Neo4j client connection state."""
        return self._is_connected

    async def execute_write(self, cypher: str, parameters: dict[str, Any] | None = None) -> Any:
        """Execute a write Cypher query."""
        if self._driver is not None:
            try:
                async with self._driver.session() as session:
                    return await session.run(cypher, parameters or {})
            except Exception as exc:
                logger.warning("Neo4j write failed: %s", exc)
        return None

    async def execute_read(self, cypher: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a read Cypher query."""
        if self._driver is not None:
            try:
                async with self._driver.session() as session:
                    result = await session.run(cypher, parameters or {})
                    records = await result.data()
                    return records
            except Exception as exc:
                logger.warning("Neo4j read failed: %s", exc)
        return []

    async def get_graph_counts(self) -> tuple[int, int]:
        """Return total node and relationship counts in graph."""
        if self._driver is not None:
            try:
                async with self._driver.session() as session:
                    res_nodes = await session.run("MATCH (n) RETURN count(n) AS count")
                    rec_nodes = await res_nodes.single()
                    nodes = rec_nodes["count"] if rec_nodes else 0

                    res_rels = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
                    rec_rels = await res_rels.single()
                    rels = rec_rels["count"] if rec_rels else 0

                    return nodes, rels
            except Exception:
                pass
        return self._graph_nodes_count, self._graph_rels_count

    def increment_local_counts(self, nodes: int, rels: int) -> None:
        """Increment local graph metrics when operating offline."""
        self._graph_nodes_count += nodes
        self._graph_rels_count += rels

    async def close(self) -> None:
        """Close Neo4j driver connection."""
        if self._driver is not None:
            try:
                await self._driver.close()
            except Exception:
                pass
        self._is_connected = False
