"""MCP Client Adapter for LangGraph workflow orchestration."""

from __future__ import annotations

import logging
from typing import Any

from medicobuddy.models.mcp import MCPResult
from medicobuddy.mcp.clinicaltrials import ClinicalTrialsConnector
from medicobuddy.mcp.medlineplus import MedlinePlusConnector
from medicobuddy.mcp.pubmed import PubMedConnector
from medicobuddy.mcp.who_crossref_ayush_cochrane import CrossrefConnector

logger = logging.getLogger(__name__)


class MCPClientAdapter:
    """Client adapter managing tool invocation and handshake readiness."""

    def __init__(self) -> None:
        self.pubmed = PubMedConnector()
        self.medlineplus = MedlinePlusConnector()
        self.clinicaltrials = ClinicalTrialsConnector()
        self.crossref = CrossrefConnector()
        self._is_initialized = False

    async def initialize(self) -> bool:
        """Perform MCP initialization and handshake check."""
        try:
            # Check readiness of core connectors
            health = {
                "pubmed": await self.pubmed.is_available(),
                "medlineplus": await self.medlineplus.is_available(),
            }
            self._is_initialized = any(health.values())
            logger.info("MCP Client Adapter initialized: %s", health)
            return self._is_initialized
        except Exception:
            logger.warning("MCP Client Adapter initialization failed")
            self._is_initialized = False
            return False

    @property
    def is_active(self) -> bool:
        """Check if MCP client handshake has succeeded."""
        return self._is_initialized

    async def search_all(self, queries: list[str], max_results_per_source: int = 3) -> list[MCPResult]:
        """Execute parallel evidence retrieval across connectors."""
        results: list[MCPResult] = []
        seen_titles: set[str] = set()

        for q in queries:
            # PubMed
            try:
                pm_res = await self.pubmed.search(q, max_results=max_results_per_source)
                for r in pm_res:
                    if r.title and r.title.lower() not in seen_titles:
                        seen_titles.add(r.title.lower())
                        results.append(r)
            except Exception as exc:
                logger.warning("PubMed search failed for '%s': %s", q, exc)

            # MedlinePlus
            try:
                mlp_res = await self.medlineplus.search(q, max_results=max_results_per_source)
                for r in mlp_res:
                    if r.title and r.title.lower() not in seen_titles:
                        seen_titles.add(r.title.lower())
                        results.append(r)
            except Exception as exc:
                logger.warning("MedlinePlus search failed for '%s': %s", q, exc)

        return results

    async def close(self) -> None:
        """Close HTTP clients."""
        await self.pubmed.close()
        await self.medlineplus.close()
        await self.clinicaltrials.close()
        await self.crossref.close()
