"""FastAPI application entry point with lifespan management.

Single-secret architecture: only GROQ_API_KEY is required.
MCP initialization is optional — failure never blocks startup.
Redis is not used. Milvus is not used.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from medicobuddy import __app_name__, __version__
from medicobuddy.api.routes import chat, consent, feedback, health
from medicobuddy.config import GIT_COMMIT_SHA, get_settings
from medicobuddy.knowledge_graph.client import Neo4jClient
from medicobuddy.retrieval.embeddings import get_embedding_provider
from medicobuddy.retrieval.vector_store import VectorStoreClient
from medicobuddy.services import RuntimeServices

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    logger.info("Starting %s v%s [%s] (commit: %s)", __app_name__, __version__, settings.app_env, GIT_COMMIT_SHA)

    # 1. Initialize Embedder (Qwen3-Embedding-0.6B local)
    embedder = get_embedding_provider(settings)
    logger.info(
        "Embedding model: %s (dim=%d, backend=%s)",
        embedder.model_name, embedder.dimension, embedder._backend,
    )

    # 2. Initialize Vector Store (pgvector only)
    vector_store = VectorStoreClient(settings)
    pg_ok = await vector_store.connect()
    if pg_ok:
        logger.info("pgvector connected, table ready")
    else:
        logger.warning("pgvector unavailable — search will fail until Postgres is reachable")

    # 3. Initialize Neo4j (Community Edition)
    neo4j = Neo4jClient(settings)
    neo4j_ok = await neo4j.connect()
    if neo4j_ok:
        logger.info("Neo4j connected")
    else:
        logger.warning("Neo4j unavailable — graph retrieval will be skipped")

    # 4. MCP initialization (optional — failure never blocks startup)
    mcp_adapter = None
    if settings.mcp_enabled:
        try:
            from medicobuddy.mcp.client import MCPClientAdapter
            mcp_adapter = MCPClientAdapter()
            await mcp_adapter.initialize()
            logger.info("MCP adapter initialized (optional enhancement)")
        except Exception as exc:
            logger.info("MCP adapter unavailable (non-fatal): %s", exc)
            mcp_adapter = None

    # 5. Compile LangGraph Workflow
    from medicobuddy.workflow.graph import create_app
    workflow = create_app()
    logger.info("LangGraph workflow compiled")

    # Store services in app state
    app.state.services = RuntimeServices(
        settings=settings,
        embedder=embedder,
        vector_store=vector_store,
        neo4j=neo4j,
        mcp=mcp_adapter,
        workflow=workflow,
        git_sha=GIT_COMMIT_SHA,
    )

    # Smoke tests — informational only, never block startup
    if pg_ok:
        smoke_res = await vector_store.smoke_test_search()
        logger.info("Vector store smoke test: %s", smoke_res)

    yield

    # Shutdown
    if hasattr(app.state, "services") and app.state.services:
        await app.state.services.close_all()
    logger.info("%s shutting down", __app_name__)


def create_fastapi_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=__app_name__,
        version=__version__,
        description=(
            "Safety-first, evidence-grounded GraphRAG wellness assistant providing "
            "general educational information and low-risk self-care guidance."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    app.include_router(consent.router, prefix="/api/v1", tags=["Consent"])
    app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])

    return app


# Module-level app for uvicorn
app = create_fastapi_app()
