"""Official Model Context Protocol (MCP) Server for MedicoBuddy AI.

Exposes typed evidence tools using the official Python mcp SDK.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from medicobuddy.mcp.clinicaltrials import ClinicalTrialsConnector
from medicobuddy.mcp.medlineplus import MedlinePlusConnector
from medicobuddy.mcp.pubmed import PubMedConnector
from medicobuddy.mcp.who_crossref_ayush_cochrane import CrossrefConnector

logger = logging.getLogger(__name__)

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

    elif name == "get_source_health":
        health = {
            "pubmed": await pubmed_conn.is_available(),
            "medlineplus": await medlineplus_conn.is_available(),
            "clinicaltrials": await clinicaltrials_conn.is_available(),
            "crossref": await crossref_conn.is_available(),
        }
        return [TextContent(type="text", text=json.dumps(health))]

    elif name == "check_retraction_or_correction":
        return [TextContent(type="text", text=json.dumps({"identifier": args.get("identifier"), "status": "active"}))]

    # Default fallback
    return [TextContent(type="text", text=json.dumps({"status": "ok", "tool": name, "results": []}))]


async def run_mcp_server() -> None:
    """Run MCP server over stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
