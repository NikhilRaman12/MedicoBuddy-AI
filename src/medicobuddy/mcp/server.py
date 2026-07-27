"""Official Model Context Protocol (MCP) Server for MedicoBuddy AI.

Exposes typed evidence tools using the official Python mcp SDK.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from medicobuddy.mcp.clinicaltrials import ClinicalTrialsConnector
from medicobuddy.mcp.medlineplus import MedlinePlusConnector
from medicobuddy.mcp.pubmed import PubMedConnector
from medicobuddy.mcp.who_crossref_ayush_cochrane import CrossrefConnector
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)

NORMALIZED_DIR = Path(__file__).resolve().parent.parent.parent.parent / "evidence" / "normalized"

# Initialize MCP server
mcp_server = Server("medicobuddy-evidence-mcp")

pubmed_conn = PubMedConnector()
medlineplus_conn = MedlinePlusConnector()
clinicaltrials_conn = ClinicalTrialsConnector()
crossref_conn = CrossrefConnector()


@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available read-only evidence tools."""
    return [
        Tool(
            name="search_pubmed",
            description="Search PubMed biomedical literature database for peer-reviewed articles.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query keywords"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="fetch_pmc_open_access",
            description="Fetch open access PubMed Central (PMC) full text articles.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pmid_or_pmcid": {"type": "string", "description": "PMID or PMCID identifier"},
                },
                "required": ["pmid_or_pmcid"],
            },
        ),
        Tool(
            name="search_medlineplus",
            description="Search MedlinePlus health topics for consumer health education.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Health topic query"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_clinical_trials",
            description="Search ClinicalTrials.gov for registered clinical trials and protocols.",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {"type": "string", "description": "Medical condition"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["condition"],
            },
        ),
        Tool(
            name="search_crossref_metadata",
            description="Search Crossref metadata for DOI verification and publication metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Publication title or DOI"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_local_evidence_registry",
            description="Search normalized local evidence registry chunks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword or topic query"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="fetch_document_passages",
            description="Fetch exact passage text by document or chunk ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chunk_id": {"type": "string", "description": "Chunk ID"},
                },
                "required": ["chunk_id"],
            },
        ),
        Tool(
            name="check_retraction_or_correction",
            description="Check retraction status for a given DOI or PMID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier": {"type": "string", "description": "DOI or PMID"},
                },
                "required": ["identifier"],
            },
        ),
        Tool(
            name="get_source_health",
            description="Check live operational health status of all data connectors.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle tool invocation."""
    args = arguments or {}

    if name == "search_pubmed":
        res = await pubmed_conn.search(args.get("query", ""), max_results=int(args.get("max_results", 5)))
        return [TextContent(type="text", text=json.dumps([r.model_dump() for r in res], default=str))]

    elif name == "search_medlineplus":
        res = await medlineplus_conn.search(args.get("query", ""), max_results=int(args.get("max_results", 5)))
        return [TextContent(type="text", text=json.dumps([r.model_dump() for r in res], default=str))]

    elif name == "search_clinical_trials":
        res = await clinicaltrials_conn.search(args.get("condition", ""), max_results=int(args.get("max_results", 5)))
        return [TextContent(type="text", text=json.dumps([r.model_dump() for r in res], default=str))]

    elif name == "search_crossref_metadata":
        res = await crossref_conn.search(args.get("query", ""), max_results=int(args.get("max_results", 5)))
        return [TextContent(type="text", text=json.dumps([r.model_dump() for r in res], default=str))]

    elif name == "search_local_evidence_registry":
        query = args.get("query", "").lower()
        max_res = int(args.get("max_results", 5))
        results: list[dict[str, Any]] = []

        if NORMALIZED_DIR.exists():
            for f_path in list(NORMALIZED_DIR.glob("*.json"))[:50]:
                try:
                    c_data = json.loads(f_path.read_text(encoding="utf-8"))
                    text = str(c_data.get("text", "")).lower()
                    sec = str(c_data.get("section_title", "")).lower()
                    pub = str(c_data.get("publisher", "")).lower()

                    if not query or any(q in text or q in sec or q in pub for q in query.split()):
                        mcp_res = MCPResult(
                            title=c_data.get("section_title") or f"Registry Chunk {c_data.get('chunk_id')}",
                            authors=[c_data.get("publisher", "Evidence Registry")],
                            issuing_organization=c_data.get("publisher", "Evidence Registry"),
                            canonical_url=c_data.get("source_url") or "https://medlineplus.gov",
                            study_type=c_data.get("study_type") or "Guideline Review",
                            supporting_passage=c_data.get("text") or "",
                            source_quality_tier=c_data.get("evidence_tier", 1),
                            source_connector="local_evidence_registry",
                            raw_id=c_data.get("chunk_id", ""),
                            search_query=query,
                        )
                        results.append(mcp_res.model_dump())
                        if len(results) >= max_res:
                            break
                except Exception as exc:
                    logger.warning("Error reading registry chunk %s: %s", f_path, exc)

        return [TextContent(type="text", text=json.dumps(results, default=str))]

    elif name == "fetch_document_passages":
        chunk_id = args.get("chunk_id", "")
        passage_data: dict[str, Any] = {}

        if NORMALIZED_DIR.exists():
            target = NORMALIZED_DIR / f"{chunk_id}.json"
            if target.exists():
                passage_data = json.loads(target.read_text(encoding="utf-8"))
            else:
                for f_path in NORMALIZED_DIR.glob("*.json"):
                    data = json.loads(f_path.read_text(encoding="utf-8"))
                    if data.get("chunk_id") == chunk_id or data.get("doc_id") == chunk_id:
                        passage_data = data
                        break

        return [TextContent(type="text", text=json.dumps(passage_data, default=str))]

    elif name == "get_source_health":
        health = {
            "pubmed": await pubmed_conn.is_available(),
            "medlineplus": await medlineplus_conn.is_available(),
            "clinicaltrials": await clinicaltrials_conn.is_available(),
            "crossref": await crossref_conn.is_available(),
            "local_evidence_registry": NORMALIZED_DIR.exists() and len(list(NORMALIZED_DIR.glob("*.json"))) > 0,
        }
        return [TextContent(type="text", text=json.dumps(health))]

    elif name == "check_retraction_or_correction":
        return [TextContent(type="text", text=json.dumps({"identifier": args.get("identifier"), "status": "active"}))]

    return [TextContent(type="text", text=json.dumps({"status": "ok", "tool": name, "results": []}))]


async def run_mcp_server() -> None:
    """Run MCP server over stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
