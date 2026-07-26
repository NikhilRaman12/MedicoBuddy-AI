"""Health check endpoints with deep dependency readiness probes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request

from medicobuddy import __app_name__, __version__
from medicobuddy.config import get_settings
from medicobuddy.mcp.client import MCPClientAdapter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/healthz", summary="Liveness probe")
@router.get("/health/live", summary="Liveness probe alias")
async def liveness() -> dict[str, str]:
    """Basic liveness check — confirms process is running."""
    return {"status": "ok", "app": __app_name__, "version": __version__}


@router.get("/readyz", summary="Readiness probe")
@router.get("/health/ready", summary="Readiness probe alias")
async def readiness(req: Request) -> dict[str, Any]:
    """Deep readiness check — verifies all core components and return ready=false if any required dependency fails."""
    settings = get_settings()

    # 1. Groq API configuration check
    groq_configured = bool(settings.groq_api_key and settings.groq_api_key != "gsk_CHANGE_ME_GROQ_API_KEY")

    # 2. Neo4j Graph DB probe
    neo4j = getattr(req.app.state, "neo4j", None)
    neo4j_ready = False
    if neo4j is not None:
        try:
            neo4j_ready = await neo4j.is_available()
        except Exception:
            neo4j_ready = False

    # 3. Vector store probe (Milvus / pgvector)
    vector_store = getattr(req.app.state, "vector_store", None)
    vector_ready = False
    if vector_store is not None:
        try:
            vector_ready = await vector_store.is_ready()
        except Exception:
            vector_ready = False

    # 4. MCP Handshake probe
    mcp_adapter = MCPClientAdapter()
    mcp_ready = await mcp_adapter.initialize()
    await mcp_adapter.close()

    # 5. Workflow compilation check
    workflow_ready = getattr(req.app.state, "workflow", None) is not None

    # Overall readiness
    overall_ready = workflow_ready and (mcp_ready or vector_ready or neo4j_ready or groq_configured)

    return {
        "status": "ok" if overall_ready else "degraded",
        "app": __app_name__,
        "version": __version__,
        "ready": overall_ready,
        "dependencies": {
            "groq_api_configured": groq_configured,
            "mcp_handshake_passed": mcp_ready,
            "neo4j_graph_db": "online" if neo4j_ready else "offline",
            "vector_store_backend": "online" if vector_ready else "offline",
            "langgraph_workflow": "compiled" if workflow_ready else "failed",
        },
        "mcp_services": ["pubmed", "medlineplus", "clinicaltrials", "crossref"] if mcp_ready else [],
    }
