"""Neo4j async client wrapper with connection pooling."""

from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from medicobuddy.config import Settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Async Neo4j client with lifecycle management."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        self._driver = AsyncGraphDatabase.driver(
            self._settings.neo4j_uri,
            auth=(self._settings.neo4j_user, self._settings.neo4j_password),
        )
        # Verify connectivity
        await self._driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", self._settings.neo4j_uri)

    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j connection closed")

    def _get_driver(self) -> AsyncDriver:
        if self._driver is None:
            msg = "Neo4j client not connected. Call connect() first."
            raise RuntimeError(msg)
        return self._driver

    async def execute_read(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a read query and return results as dicts."""
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records  # type: ignore[return-value]

    async def execute_write(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a write query."""
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records  # type: ignore[return-value]

    async def execute_write_batch(self, queries: list[str]) -> None:
        """Execute multiple write queries in a single session."""
        driver = self._get_driver()
        async with driver.session() as session:
            for query in queries:
                await session.run(query)
        logger.info("Executed %d write queries", len(queries))

    async def init_schema(self) -> None:
        """Create constraints and indexes from schema definitions."""
        from medicobuddy.knowledge_graph.schema import SCHEMA_CONSTRAINTS, SCHEMA_INDEXES

        all_statements = SCHEMA_CONSTRAINTS + SCHEMA_INDEXES
        await self.execute_write_batch(all_statements)
        logger.info("Neo4j schema initialised (%d statements)", len(all_statements))
