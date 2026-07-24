"""WHO publications, Crossref, AYUSH, and Cochrane MCP connectors.

WHO, AYUSH, and Cochrane use adapter interfaces — marked as limited availability
where official APIs are restricted. Crossref uses the public REST API.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from medicobuddy.mcp.base import MCPConnector
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)


class WHOConnector(MCPConnector):
    """WHO publications connector (adapter interface).

    WHO does not provide a general-purpose search API for all publications.
    This connector uses WHO IRIS (Institutional Repository) where available,
    and is clearly marked as having limited availability.
    """

    connector_name = "who"

    async def is_available(self) -> bool:
        try:
            await self._get("https://apps.who.int/iris/rest/items?limit=1")
            return True
        except Exception:
            logger.warning("WHO connector unavailable — limited API access")
            return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Search WHO IRIS for guidance documents."""
        try:
            params = {"query": query, "limit": str(max_results)}
            data = await self._get(
                "https://apps.who.int/iris/rest/items", params=params
            )
        except Exception:
            logger.info("WHO search unavailable; returning empty results")
            return []

        results: list[MCPResult] = []
        for item in data if isinstance(data, list) else []:
            title = item.get("name", "")
            handle = item.get("handle", "")
            results.append(
                MCPResult(
                    title=title,
                    issuing_organization="World Health Organization",
                    canonical_url=f"https://apps.who.int/iris/handle/{handle}" if handle else "",
                    study_type="clinical_guideline",
                    source_quality_tier=1,
                    source_connector=self.connector_name,
                    raw_id=handle,
                    search_query=query,
                    retrieval_timestamp=datetime.now(timezone.utc),
                )
            )
        return results


class CrossrefConnector(MCPConnector):
    """Crossref metadata API connector for DOI resolution and enrichment."""

    connector_name = "crossref"

    async def is_available(self) -> bool:
        try:
            await self._get("https://api.crossref.org/works?rows=1")
            return True
        except Exception:
            logger.warning("Crossref connector unavailable")
            return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Search Crossref for scholarly works."""
        params = {
            "query": query,
            "rows": str(max_results),
            "sort": "relevance",
            "order": "desc",
        }

        try:
            data = await self._get("https://api.crossref.org/works", params=params)
        except Exception:
            logger.warning("Crossref search failed for query: %s", query)
            return []

        results: list[MCPResult] = []
        items = data.get("message", {}).get("items", [])

        for item in items[:max_results]:
            title_parts = item.get("title", [])
            title = title_parts[0] if title_parts else ""
            doi = item.get("DOI", "")

            authors: list[str] = []
            for author in item.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                authors.append(f"{given} {family}".strip())

            # Publication date
            date_parts = item.get("published-print", {}).get("date-parts", [[]])
            if not date_parts[0]:
                date_parts = item.get("published-online", {}).get("date-parts", [[]])
            pub_date = "-".join(str(p) for p in date_parts[0]) if date_parts[0] else ""

            # Type
            work_type = item.get("type", "unknown")

            results.append(
                MCPResult(
                    title=title,
                    authors=authors,
                    publication_date=pub_date,
                    doi=doi,
                    canonical_url=f"https://doi.org/{doi}" if doi else "",
                    study_type=work_type,
                    source_quality_tier=4,
                    source_connector=self.connector_name,
                    raw_id=doi,
                    search_query=query,
                    retrieval_timestamp=datetime.now(timezone.utc),
                    usage_licence=item.get("license", [{}])[0].get("URL", "")
                    if item.get("license")
                    else "",
                )
            )

        return results


class AYUSHConnector(MCPConnector):
    """Ministry of AYUSH Research Portal connector (adapter interface).

    The AYUSH portal does not provide a public REST API. This connector
    implements the standard interface and is clearly marked as unavailable
    until an authorized access method is established.
    """

    connector_name = "ayush"

    async def is_available(self) -> bool:
        logger.info(
            "AYUSH connector: No public API available. "
            "Implement authorized access when available."
        )
        return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Placeholder — returns empty results with unavailability notice."""
        logger.info(
            "AYUSH search unavailable (no public API). Query: %s", query
        )
        return []


class CochraneConnector(MCPConnector):
    """Cochrane Library connector (adapter interface).

    Cochrane abstracts may be accessed where legally permitted. Full-text
    requires subscription. This connector uses publicly available metadata only.
    """

    connector_name = "cochrane"

    async def is_available(self) -> bool:
        logger.info(
            "Cochrane connector: Limited to publicly available metadata. "
            "Full-text requires Cochrane Library subscription."
        )
        return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Placeholder — implement with authorized Cochrane API access."""
        logger.info(
            "Cochrane search: Limited availability. Query: %s", query
        )
        return []
