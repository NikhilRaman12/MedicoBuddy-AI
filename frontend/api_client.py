"""MedicoBuddy AI — Typed API Client Module.

Provides robust, exception-safe HTTP calls to the FastAPI backend endpoints:
- POST /api/v1/chat
- GET /health/live
- GET /health/ready
- GET /health/dependencies
- DELETE /api/v1/chat/thread/{thread_id}

Never raises uncaught HTTP exceptions to the UI. Returns clean error dicts on timeout or network error.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Default endpoint URLs with environment overrides
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api/v1")
HEALTH_LIVE_URL = os.getenv("HEALTH_LIVE_URL", "http://127.0.0.1:8000/health/live")
HEALTH_READY_URL = os.getenv("HEALTH_READY_URL", "http://127.0.0.1:8000/health/ready")
HEALTH_DEPS_URL = os.getenv("HEALTH_DEPS_URL", "http://127.0.0.1:8000/health/dependencies")

DEFAULT_TIMEOUT_SEC = 60.0


def check_health_live() -> dict[str, Any]:
    """Check GET /health/live endpoint."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(HEALTH_LIVE_URL)
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("GET /health/live failed: %s", exc)
    return {"status": "unreachable", "live": False}


def check_health_ready() -> dict[str, Any]:
    """Check GET /health/ready endpoint."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(HEALTH_READY_URL)
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("GET /health/ready failed: %s", exc)
    return {"status": "unreachable", "ready": False}


def check_health_dependencies() -> dict[str, Any]:
    """Check GET /health/dependencies endpoint."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(HEALTH_DEPS_URL)
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("GET /health/dependencies failed: %s", exc)
    return {"overall": "unreachable"}


def send_chat_message(payload: dict[str, Any]) -> dict[str, Any]:
    """Send chat request to POST /api/v1/chat.

    Returns the response JSON dictionary or an error dictionary.
    """
    url = f"{API_BASE}/chat"
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT_SEC) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error("POST /chat returned status %d: %s", resp.status_code, resp.text)
                return {
                    "error": f"Backend service returned status {resp.status_code}",
                    "status_code": resp.status_code,
                    "summary": "Grounded answer is temporarily unavailable. Please retry after backend service recovers.",
                    "action_table": [],
                    "citations": [],
                }
    except httpx.TimeoutException:
        logger.error("POST /chat timed out after %.1fs", DEFAULT_TIMEOUT_SEC)
        return {
            "error": "Request timed out",
            "summary": "The request timed out while waiting for evidence retrieval. Please retry.",
            "action_table": [],
            "citations": [],
        }
    except Exception as exc:
        logger.error("POST /chat failed with exception: %s", exc)
        return {
            "error": str(exc),
            "summary": "Connection error: Could not reach the MedicoBuddy AI evidence service.",
            "action_table": [],
            "citations": [],
        }


def delete_thread_history(thread_id: str) -> bool:
    """Send DELETE /api/v1/chat/thread/{thread_id} request."""
    url = f"{API_BASE}/chat/thread/{thread_id}"
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.delete(url)
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("DELETE /chat/thread failed: %s", exc)
        return False
