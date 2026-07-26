"""MedlinePlus / NLM consumer-health MCP connector with robust XML parsing."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
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
            params = {"db": "healthTopics", "term": "headache", "retmax": "1"}
            xml_str = await self._get_xml(f"{MEDLINEPLUS_BASE}/query", params=params)
            return "<nlmSearchResult" in xml_str or "<document" in xml_str
        except Exception:
            logger.warning("MedlinePlus connector unavailable")
            return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Search MedlinePlus health topics parsing official NLM XML format."""
        params = {
            "db": "healthTopics",
            "term": query,
            "retmax": str(max_results),
        }

        try:
            xml_text = await self._get_xml(f"{MEDLINEPLUS_BASE}/query", params=params)
        except Exception:
            logger.warning("MedlinePlus XML search failed for query: %s", query)
            return []

        results: list[MCPResult] = []

        try:
            root = ET.fromstring(xml_text)
            # MedlinePlus XML returns <document url="..."> tags under <list>
            docs = root.findall(".//document")
            for doc in docs[:max_results]:
                url = doc.get("url", "")
                title = ""
                snippet = ""

                for child in doc.findall("content"):
                    name = child.get("name")
                    if name == "title" and child.text:
                        # Clean XML markup inside title
                        title = child.text.replace("<span>", "").replace("</span>", "").replace("<b>", "").replace("</b>", "").strip()
                    elif name == "FullSummary" and child.text:
                        snippet = child.text.replace("<span>", "").replace("</span>", "").replace("<b>", "").replace("</b>", "").strip()

                if not snippet:
                    snippet_elem = doc.find(".//snippet")
                    if snippet_elem is not None and snippet_elem.text:
                        snippet = snippet_elem.text.strip()

                if title or snippet:
                    results.append(
                        MCPResult(
                            title=title or "MedlinePlus Health Topic",
                            authors=["National Library of Medicine"],
                            issuing_organization="National Library of Medicine (NLM)",
                            canonical_url=url or "https://medlineplus.gov",
                            study_type="consumer_health_resource",
                            supporting_passage=snippet[:500] if snippet else title,
                            source_quality_tier=1,
                            source_connector=self.connector_name,
                            raw_id=url,
                            search_query=query,
                            retrieval_timestamp=datetime.now(timezone.utc),
                        )
                    )
        except Exception as exc:
            logger.warning("Failed to parse MedlinePlus XML output: %s", exc)

        return results
