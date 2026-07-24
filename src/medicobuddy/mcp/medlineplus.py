"""MedlinePlus / NLM consumer-health MCP connector."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from medicobuddy.mcp.base import MCPConnector
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)

MEDLINEPLUS_BASE = "https://wsearch.nlm.nih.gov/ws"


class MedlinePlusConnector(MCPConnector):
    """Read-only connector for MedlinePlus health topics."""

    connector_name = "medlineplus"

    async def is_available(self) -> bool:
        try:
            params = {"db": "healthTopics", "term": "test", "retmax": "1"}
            await self._get(f"{MEDLINEPLUS_BASE}/query", params=params)
            return True
        except Exception:
            logger.warning("MedlinePlus connector unavailable")
            return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Search MedlinePlus health topics."""
        params = {
            "db": "healthTopics",
            "term": query,
            "retmax": str(max_results),
        }

        try:
            data = await self._get(f"{MEDLINEPLUS_BASE}/query", params=params)
        except Exception:
            logger.warning("MedlinePlus search failed for query: %s", query)
            return []

        results: list[MCPResult] = []
        nlm_results = data.get("nlmSearchResult", {})
        items = nlm_results.get("list", [])

        for item in items[:max_results]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("knowledgeUrl", "") or item.get("url", "")

            results.append(
                MCPResult(
                    title=title,
                    authors=[],
                    issuing_organization="National Library of Medicine",
                    canonical_url=url,
                    study_type="consumer_health_resource",
                    supporting_passage=snippet,
                    source_quality_tier=1,
                    source_connector=self.connector_name,
                    raw_id=url,
                    search_query=query,
                    retrieval_timestamp=datetime.now(timezone.utc),
                )
            )

        return results
