"""PubMed / PubMed Central MCP connector via NCBI E-utilities."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from xml.etree import ElementTree

from medicobuddy.mcp.base import MCPConnector
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedConnector(MCPConnector):
    """Read-only connector for PubMed via NCBI E-utilities API."""

    connector_name = "pubmed"

    def __init__(
        self,
        api_key: str = "",
        email: str = "",
        tool_name: str = "medicobuddy",
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._api_key = api_key
        self._email = email
        self._tool_name = tool_name

    def _base_params(self) -> dict[str, str]:
        params: dict[str, str] = {"tool": self._tool_name}
        if self._api_key:
            params["api_key"] = self._api_key
        if self._email:
            params["email"] = self._email
        return params

    async def is_available(self) -> bool:
        try:
            params = {**self._base_params(), "db": "pubmed", "retmode": "json"}
            await self._get(f"{EUTILS_BASE}/einfo.fcgi", params=params)
            return True
        except Exception:
            logger.warning("PubMed connector unavailable")
            return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Search PubMed and fetch article details."""
        # Step 1: esearch to get PMIDs
        search_params = {
            **self._base_params(),
            "db": "pubmed",
            "term": query,
            "retmax": str(max_results),
            "retmode": "json",
            "sort": "relevance",
        }

        search_data = await self._get(f"{EUTILS_BASE}/esearch.fcgi", params=search_params)
        id_list = search_data.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            return []

        # Step 2: efetch to get article details
        fetch_params = {
            **self._base_params(),
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
            "rettype": "abstract",
        }

        xml_text = await self._get_xml(f"{EUTILS_BASE}/efetch.fcgi", params=fetch_params)
        return self._parse_articles(xml_text, query)

    def _parse_articles(self, xml_text: str, query: str) -> list[MCPResult]:
        """Parse PubMed XML response into MCPResult list."""
        results: list[MCPResult] = []

        try:
            root = ElementTree.fromstring(xml_text)  # noqa: S314
        except ElementTree.ParseError:
            logger.error("Failed to parse PubMed XML response")
            return results

        for article in root.findall(".//PubmedArticle"):
            try:
                result = self._parse_single_article(article, query)
                if result:
                    results.append(result)
            except Exception:
                logger.warning("Failed to parse a PubMed article", exc_info=True)

        return results

    def _parse_single_article(
        self, article: ElementTree.Element, query: str
    ) -> MCPResult | None:
        """Parse a single PubmedArticle element."""
        medline = article.find(".//MedlineCitation")
        if medline is None:
            return None

        pmid_elem = medline.find("PMID")
        pmid = pmid_elem.text if pmid_elem is not None and pmid_elem.text else ""

        art_elem = medline.find("Article")
        if art_elem is None:
            return None

        # Title
        title_elem = art_elem.find("ArticleTitle")
        title = title_elem.text if title_elem is not None and title_elem.text else ""

        # Authors
        authors: list[str] = []
        for author in art_elem.findall(".//Author"):
            last = author.find("LastName")
            fore = author.find("ForeName")
            if last is not None and last.text:
                name = last.text
                if fore is not None and fore.text:
                    name = f"{fore.text} {last.text}"
                authors.append(name)

        # Publication date
        pub_date_elem = art_elem.find(".//PubDate")
        pub_date = ""
        if pub_date_elem is not None:
            year = pub_date_elem.find("Year")
            month = pub_date_elem.find("Month")
            if year is not None and year.text:
                pub_date = year.text
                if month is not None and month.text:
                    pub_date = f"{year.text}-{month.text}"

        # Abstract
        abstract_parts: list[str] = []
        for abs_text in art_elem.findall(".//AbstractText"):
            if abs_text.text:
                label = abs_text.get("Label", "")
                prefix = f"{label}: " if label else ""
                abstract_parts.append(f"{prefix}{abs_text.text}")
        abstract = " ".join(abstract_parts)

        # DOI
        doi = ""
        for eid in art_elem.findall(".//ELocationID"):
            if eid.get("EIdType") == "doi" and eid.text:
                doi = eid.text
                break

        # Publication type (study design hint)
        pub_types: list[str] = []
        for pt in art_elem.findall(".//PublicationType"):
            if pt.text:
                pub_types.append(pt.text)
        study_type = self._infer_study_type(pub_types)

        # Check retraction
        retraction = "none"
        for pt in pub_types:
            if "retract" in pt.lower():
                retraction = "retracted"
                break

        return MCPResult(
            title=title,
            authors=authors,
            publication_date=pub_date,
            doi=doi,
            pmid=pmid,
            canonical_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            study_type=study_type,
            supporting_passage=abstract[:1000] if abstract else "",
            retraction_status=retraction,
            source_quality_tier=self._infer_tier(study_type),
            source_connector=self.connector_name,
            raw_id=pmid,
            search_query=query,
            retrieval_timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def _infer_study_type(pub_types: list[str]) -> str:
        """Infer study design from PubMed publication types."""
        text = " ".join(pub_types).lower()
        if "meta-analysis" in text:
            return "meta_analysis"
        if "systematic review" in text:
            return "systematic_review"
        if "randomized controlled trial" in text:
            return "randomized_controlled_trial"
        if "clinical trial" in text:
            return "clinical_trial"
        if "review" in text:
            return "narrative_review"
        if "case report" in text:
            return "case_report"
        if "guideline" in text or "practice guideline" in text:
            return "clinical_guideline"
        return "unknown"

    @staticmethod
    def _infer_tier(study_type: str) -> int:
        """Map study type to evidence tier."""
        tier_map = {
            "clinical_guideline": 1,
            "systematic_review": 2,
            "meta_analysis": 2,
            "randomized_controlled_trial": 3,
            "clinical_trial": 3,
            "cohort_study": 4,
            "case_report": 5,
            "narrative_review": 6,
        }
        return tier_map.get(study_type, 7)
