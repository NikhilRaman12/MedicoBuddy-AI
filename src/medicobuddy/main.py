"""FastAPI application entry point with lifespan management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from medicobuddy import __app_name__, __version__
from medicobuddy.api.routes import chat, consent, feedback, health
from medicobuddy.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    logger.info("Starting %s v%s [%s]", __app_name__, __version__, settings.app_env)

    # Startup: initialize connections (graceful if unavailable)
    try:
        from medicobuddy.knowledge_graph.client import Neo4jClient
        neo4j = Neo4jClient(settings)
        await neo4j.connect()
        app.state.neo4j = neo4j
    except Exception:
        logger.warning("Neo4j not available — graph features disabled")
        app.state.neo4j = None

    try:
        from medicobuddy.retrieval.vector_store import VectorStoreClient
        vector = VectorStoreClient(settings)
        await vector.connect()
        app.state.vector_store = vector
    except Exception:
        logger.warning("Qdrant not available — vector search disabled")
        app.state.vector_store = None

    # Create the LangGraph workflow
    try:
        from medicobuddy.workflow.graph import create_app
        app.state.workflow = create_app()
        logger.info("LangGraph workflow compiled")
    except Exception:
        logger.error("Failed to compile LangGraph workflow", exc_info=True)
        app.state.workflow = None

    yield

    # Shutdown
    if hasattr(app.state, "neo4j") and app.state.neo4j:
        await app.state.neo4j.close()
    if hasattr(app.state, "vector_store") and app.state.vector_store:
        await app.state.vector_store.close()
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
        allow_methods=["GET", "POST"],
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
