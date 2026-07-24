"""Standardised MCP connector result schema."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MCPResult(BaseModel):
    """Standardised result from any MCP data connector.

    Every MCP connector must return results in this format to ensure
    uniform evidence processing downstream.
    """

    title: str
    authors: list[str] = Field(default_factory=list)
    issuing_organization: str = ""
    publication_date: str = ""
    doi: str = ""
    pmid: str = ""
    trial_id: str = ""
    canonical_url: str = ""
    study_type: str = ""
    population: str = ""
    sample_size: int | None = None
    intervention: str = ""
    outcome: str = ""
    limitations: str = ""
    retraction_status: str = "unknown"
    source_quality_tier: int = Field(default=7, ge=1, le=7)
    retrieval_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    supporting_passage: str = ""
    usage_licence: str = ""

    # ── Connector metadata ───────────────────────────────────
    source_connector: str = Field(description="Name of the MCP connector that produced this result")
    raw_id: str = Field(default="", description="Original ID from the source system")
    search_query: str = Field(default="", description="Query that produced this result")
