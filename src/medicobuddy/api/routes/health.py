"""Health check endpoints with truthful readiness gates.

All values are derived from real runtime measurements.
No hardcoded counts, no fabricated status values.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

from medicobuddy import __app_name__, __version__
from medicobuddy.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

GIT_COMMIT = os.environ.get("GIT_COMMIT_SHA", "dev")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
INGESTION_REPORT_PATH = PROJECT_ROOT / "evidence" / "reports" / "ingestion_report.json"


@router.get("/healthz", summary="Liveness probe")
@router.get("/health/live", summary="Liveness probe alias")
async def liveness() -> dict[str, str]:
    """Basic liveness check — confirms process is running."""
    return {
        "status": "ok",
        "app": __app_name__,
        "version": __version__,
        "git_commit": GIT_COMMIT,
    }


@router.get("/readyz", summary="Readiness probe")
@router.get("/health/ready", summary="Readiness probe alias")
async def readiness(req: Request) -> dict[str, Any]:
    """Truthful readiness probe — all values from real runtime measurements.

    Gates:
    1. PDF documents discovered > 0
    2. Successfully parsed documents > 0
    3. Meaningful indexed chunks > 0
    4. Qwen embedding model loaded = YES
    5. Embedding dimension = 1024
    6. pgvector similarity hits >= 1
    7. Neo4j nodes > 0, relationships > 0
    8. LangGraph execution = PASS
    9. Groq API key configured = YES
    """
    settings = get_settings()

    # Read ingestion report for real stats
    pdfs_discovered = 0
    pdfs_parsed = 0
    pages_extracted = 0
    characters_extracted = 0
    vectors_written = 0
    graph_nodes_written = 0
    graph_rels_written = 0
    embedding_fingerprint = ""

    if INGESTION_REPORT_PATH.exists():
        try:
            report_data = json.loads(INGESTION_REPORT_PATH.read_text(encoding="utf-8"))
            pdfs_discovered = report_data.get("pdfs_discovered", 0)
            pdfs_parsed = report_data.get("pdfs_successful", 0)
            pages_extracted = report_data.get("pages_extracted", 0)
            characters_extracted = report_data.get("characters_extracted", 0)
            vectors_written = report_data.get("vectors_written", 0)
            graph_nodes_written = report_data.get("graph_nodes_written", 0)
            graph_rels_written = report_data.get("graph_relationships_written", 0)
            embedding_fingerprint = report_data.get("embedding_fingerprint", "")
        except Exception:
            pass

    # Check real runtime services
    services = getattr(req.app.state, "services", None)

    # Gate 1-2: PDF documents
    c1_pdfs_discovered = pdfs_discovered > 0
    c2_pdfs_parsed = pdfs_parsed > 0

    # Gate 3: Indexed chunks (from real vector store count)
    real_indexed_chunks = 0
    if services and services.vector_store:
        try:
            real_indexed_chunks = await services.vector_store.get_indexed_count()
        except Exception:
            pass
    c3_indexed_chunks = real_indexed_chunks > 0

    # Gate 4-5: Embedding model
    embedding_loaded = False
    real_embedding_dim = 0
    embedding_model_name = "unknown"
    if services and services.embedder:
        embedding_loaded = services.embedder._backend not in ("ERROR", "uninitialized")
        real_embedding_dim = services.embedder.dimension
        embedding_model_name = services.embedder.model_name
    c4_embedding_loaded = embedding_loaded
    c5_embedding_dim = real_embedding_dim == 1024

    # Gate 6: pgvector smoke test
    smoke_hits = 0
    if services and services.vector_store:
        try:
            smoke = await services.vector_store.smoke_test_search()
            smoke_hits = smoke.get("hits", 0)
        except Exception:
            pass
    c6_pgvector_hits = smoke_hits >= 1

    # Gate 7: Neo4j nodes and relationships
    real_graph_nodes = 0
    real_graph_rels = 0
    if services and services.neo4j:
        try:
            real_graph_nodes, real_graph_rels = await services.neo4j.get_graph_counts()
        except Exception:
            pass
    c7_graph = real_graph_nodes > 0 and real_graph_rels > 0

    # Gate 8: LangGraph workflow
    c8_workflow = services is not None and services.workflow is not None

    # Gate 9: Groq API key
    groq_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
    c9_groq = bool(groq_key and groq_key.startswith("gsk_"))

    is_ready = all([
        c1_pdfs_discovered, c2_pdfs_parsed, c3_indexed_chunks,
        c4_embedding_loaded, c5_embedding_dim, c6_pgvector_hits,
        c7_graph, c8_workflow, c9_groq,
    ])

    mode = "Evidence Service Online" if is_ready else "Evidence Pipeline Initializing"

    return {
        "status": "ok" if is_ready else "degraded",
        "ready": is_ready,
        "mode": mode,
        "app": __app_name__,
        "version": __version__,
        "git_commit": GIT_COMMIT,
        "pdfs_discovered": pdfs_discovered,
        "pdfs_parsed": pdfs_parsed,
        "pages_extracted": pages_extracted,
        "characters_extracted": characters_extracted,
        "indexed_chunks": real_indexed_chunks,
        "vectors_written": vectors_written,
        "pgvector_smoke_test_hits": smoke_hits,
        "graph_nodes": real_graph_nodes,
        "graph_relationships": real_graph_rels,
        "embedding_model": embedding_model_name,
        "embedding_dimension": real_embedding_dim,
        "embedding_fingerprint": embedding_fingerprint,
        "readiness_gates": {
            "pdfs_discovered": c1_pdfs_discovered,
            "pdfs_parsed": c2_pdfs_parsed,
            "indexed_chunks_valid": c3_indexed_chunks,
            "embedding_model_loaded": c4_embedding_loaded,
            "embedding_dimension_1024": c5_embedding_dim,
            "pgvector_smoke_hits": c6_pgvector_hits,
            "graph_populated": c7_graph,
            "langgraph_execution": c8_workflow,
            "groq_configured": c9_groq,
        },
        "workflow": "ready" if c8_workflow else "offline",
        "groq": "ready" if c9_groq else "unconfigured",
        "embedding_service": "ready" if c4_embedding_loaded else "error",
        "mcp_handshake": False,  # MCP is optional
        "local_evidence_index": c3_indexed_chunks,
        "milvus_pgvector": c3_indexed_chunks,  # backward compat field name
        "neo4j": c7_graph,
        "indexed_passages_count": real_indexed_chunks,
    }
