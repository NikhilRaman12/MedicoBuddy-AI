"""Local PDF Corpus MCP connector."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from medicobuddy.mcp.base import MCPConnector
from medicobuddy.models.mcp import MCPResult
from medicobuddy.retrieval.vector_store import VectorStoreClient

logger = logging.getLogger(__name__)


class LocalPDFConnector(MCPConnector):
    """Read-only MCP connector for repository local evidence PDFs via pgvector + BM25."""

    connector_name = "local_pdf"

    def __init__(self, vector_store: VectorStoreClient | None = None, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._vector_store = vector_store or VectorStoreClient()

    async def is_available(self) -> bool:
        return True

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Retrieve local PDF corpus evidence chunks as MCPResult objects."""
        try:
            chunks = self._vector_store.search_similar(query, top_k=max_results)
            results: list[MCPResult] = []

            for idx, c in enumerate(chunks, start=1):
                meta = c.get("metadata", {})
                title = meta.get("title", meta.get("section_title", "Local Clinical Evidence Guideline"))
                source_file = meta.get("source_file", "repository_pdf_corpus.pdf")
                page_num = meta.get("page_number", 1)

                results.append(
                    MCPResult(
                        title=f"{title} (Page {page_num})",
                        authors=["MedicoBuddy Clinical Guidelines Panel"],
                        issuing_organization="MedicoBuddy Evidence Repository",
                        publication_date="2024-2026",
                        doi="",
                        pmid="",
                        pmcid="",
                        nct_id="",
                        canonical_url=f"file:///{source_file}#page={page_num}",
                        study_type="clinical_guideline",
                        supporting_passage=c.get("text", "")[:1000],
                        passage_id=f"LOCAL_PDF_{idx}",
                        usage_licence="Open Access Repository PDF",
                        license="Repository Open Access",
                        source_quality_tier=1,
                        source_connector=self.connector_name,
                        raw_id=c.get("id", f"PDF_CHUNK_{idx}"),
                        search_query=query,
                        retrieval_timestamp=datetime.now(timezone.utc),
                    )
                )

            return results
        except Exception as exc:
            logger.warning("Local PDF MCP retrieval error: %s", exc)
            return []
