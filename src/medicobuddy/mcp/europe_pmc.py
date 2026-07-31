"""Europe PMC MCP connector via Europe PMC REST API."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from medicobuddy.mcp.base import MCPConnector
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)

EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


class EuropePMCConnector(MCPConnector):
    """Read-only connector for Europe PMC via official REST API."""

    connector_name = "europe_pmc"

    async def is_available(self) -> bool:
        try:
            params = {"query": "headache", "format": "json", "pageSize": "1"}
            data = await self._get(EUROPE_PMC_BASE, params=params)
            return bool(data.get("hitCount", 0) > 0)
        except Exception:
            logger.warning("Europe PMC connector unavailable")
            return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Search Europe PMC and return structured results with PMCID, DOI, and open access license."""
        params = {
            "query": f"{query} (SRC:MED OR OPEN_ACCESS:y)",
            "format": "json",
            "pageSize": str(max_results),
            "resultType": "core",
        }

        try:
            data = await self._get(EUROPE_PMC_BASE, params=params)
            results_list = data.get("resultList", {}).get("result", [])
            return [self._parse_result(item, query) for item in results_list if item]
        except Exception as exc:
            logger.warning("Europe PMC search error: %s", exc)
            return []

    def _parse_result(self, item: dict[str, Any], query: str) -> MCPResult:
        title = item.get("title", "")
        authors_raw = item.get("authorString", "")
        authors = [a.strip() for a in authors_raw.split(",") if a.strip()] if authors_raw else []

        pmid = item.get("pmid", "")
        pmcid = item.get("pmcid", "")
        doi = item.get("doi", "")
        pub_year = str(item.get("pubYear", ""))

        abstract = item.get("abstractText", "")
        isOpenAccess = item.get("isOpenAccess", "N") == "Y"
        license_str = item.get("license", "Open Access" if isOpenAccess else "Public Permitted")

        url = f"https://europepmc.org/article/PMC/{pmcid}" if pmcid else (f"https://europepmc.org/article/MED/{pmid}" if pmid else "")

        return MCPResult(
            title=title,
            authors=authors[:5],
            publication_date=pub_year,
            doi=doi,
            pmid=pmid,
            pmcid=pmcid,
            canonical_url=url,
            study_type=item.get("pubType", "clinical_evidence"),
            supporting_passage=abstract[:1000] if abstract else title,
            usage_licence=license_str,
            license=license_str,
            source_quality_tier=3 if isOpenAccess else 4,
            source_connector=self.connector_name,
            raw_id=pmcid or pmid or doi,
            search_query=query,
            retrieval_timestamp=datetime.now(timezone.utc),
        )
