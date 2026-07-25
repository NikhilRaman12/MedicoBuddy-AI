"""Groq LLM manager for MedicoBuddy — handles ChatGroq initialization.

Strictly relies on Groq API — no other third-party LLM providers.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from medicobuddy.config import Settings, get_settings

logger = logging.getLogger(__name__)


def get_llm(settings: Settings | None = None) -> Any:
    """Instantiate and return the Groq Chat model via LangChain.

    Primary Model: llama-3.3-70b-versatile
    Fallbacks: mixtral-8x7b-32768, qwen-2.5-72b-instruct
    """
    if settings is None:
        settings = get_settings()

    api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "gsk_CHANGE_ME_GROQ_API_KEY":
        logger.info("GROQ_API_KEY not set or placeholder — running in deterministic safety fallback mode")
        return None

    try:
        from langchain_groq import ChatGroq

        model_name = settings.groq_model_name or "llama-3.3-70b-versatile"
        logger.info("Initializing Groq LLM model: %s", model_name)

        return ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
    except Exception:
        logger.warning("Failed to initialize ChatGroq client", exc_info=True)
        return None
