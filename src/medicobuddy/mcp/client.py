"""Official Allowlisted MCP Client Adapter for MedicoBuddy AI.

Implements allowlisted evidence connectors for:
1. PubMed / PMC
2. Europe PMC
3. ClinicalTrials.gov
4. Local PDF Corpus

No unrestricted web-scraping or fetch_url tools. All servers obey paywalls,
robots rules, open-access licenses, and rate limits.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from medicobuddy.mcp.clinicaltrials import ClinicalTrialsConnector
from medicobuddy.mcp.europe_pmc import EuropePMCConnector
from medicobuddy.mcp.local_pdf import LocalPDFConnector
from medicobuddy.mcp.pubmed import PubMedConnector
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)


class MCPClientAdapter:
    """Client adapter calling allowlisted evidence connectors concurrently."""

    def __init__(self) -> None:
        self.pubmed = PubMedConnector()
        self.europe_pmc = EuropePMCConnector()
        self.clinical_trials = ClinicalTrialsConnector()
        self.local_pdf = LocalPDFConnector()
        self._is_initialized = False

    async def initialize(self) -> bool:
        """Initialize allowlisted connectors."""
        self._is_initialized = True
        logger.info("Allowlisted MCP ClientAdapter initialized successfully")
        return True

    @property
    def is_active(self) -> bool:
        return self._is_initialized

    async def search_all(
        self,
        queries: list[str],
        max_results_per_source: int = 3,
    ) -> tuple[list[MCPResult], dict[str, str], list[str]]:
        """Concurrent evidence retrieval across allowlisted MCP connectors."""
        all_results: list[MCPResult] = []
        retrieval_status: dict[str, str] = {}
        dependency_errors: list[str] = []
        seen_titles: set[str] = set()

        q = queries[0] if queries else "headache"

        connectors: list[tuple[str, Any]] = [
            ("local_pdf", self.local_pdf.search(q, max_results_per_source)),
            ("pubmed", self.pubmed.search(q, max_results_per_source)),
            ("europe_pmc", self.europe_pmc.search(q, max_results_per_source)),
            ("clinical_trials", self.clinical_trials.search(q, max_results_per_source)),
        ]

        tasks = [c_task for _, c_task in connectors]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        for (c_name, _), res_or_exc in zip(connectors, gathered):
            if isinstance(res_or_exc, Exception):
                retrieval_status[c_name] = f"failed ({res_or_exc})"
                dependency_errors.append(f"{c_name}: {res_or_exc}")
            elif isinstance(res_or_exc, list):
                retrieval_status[c_name] = f"success ({len(res_or_exc)} items)"
                for r in res_or_exc:
                    norm_title = r.title.strip().lower()
                    if norm_title and norm_title not in seen_titles:
                        seen_titles.add(norm_title)
                        all_results.append(r)

        return all_results, retrieval_status, dependency_errors

    async def close(self) -> None:
        """Close client resources."""
        self._is_initialized = False
