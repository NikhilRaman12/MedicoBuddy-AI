"""Abstract MCP connector base class with shared HTTP, retry, and rate-limit logic."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)

# Default request timeout in seconds
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


class MCPConnector(ABC):
    """Base class for all MCP data connectors.

    Every connector must:
    1. Implement search() returning standardised MCPResult list
    2. Respect rate limits and robots.txt
    3. Never bypass paywalls or authentication
    4. Return real data only — never fabricate results
    """

    connector_name: str = "base"

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
                headers={"User-Agent": "MedicoBuddy/0.1 (health-education-tool)"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """HTTP GET with retry logic."""
        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code == 429:  # noqa: PLR2004
                    logger.warning(
                        "%s: Rate limited (attempt %d/%d)",
                        self.connector_name, attempt, self._max_retries,
                    )
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                elif exc.response.status_code >= 500:  # noqa: PLR2004
                    logger.warning(
                        "%s: Server error %d (attempt %d/%d)",
                        self.connector_name, exc.response.status_code,
                        attempt, self._max_retries,
                    )
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
            except httpx.RequestError as exc:
                last_error = exc
                logger.warning(
                    "%s: Request error (attempt %d/%d): %s",
                    self.connector_name, attempt, self._max_retries, exc,
                )
                import asyncio
                await asyncio.sleep(2 ** attempt)

        msg = f"{self.connector_name}: All {self._max_retries} retries exhausted"
        raise httpx.RequestError(msg) from last_error

    async def _get_xml(self, url: str, params: dict[str, Any] | None = None) -> str:
        """HTTP GET returning raw XML text."""
        client = await self._get_client()
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.text

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Search the data source and return standardised results.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.

        Returns:
            List of MCPResult objects.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the connector is available and configured."""
