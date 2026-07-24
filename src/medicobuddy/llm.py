"""Groq LLM manager for MedicoBuddy — handles ChatGroq initialization and fallback."""

from __future__ import annotations

import logging
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

    provider = settings.llm_provider.lower()

    if provider == "groq" or settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq

            logger.info("Initializing Groq LLM model: %s", settings.groq_model_name)
            return ChatGroq(
                groq_api_key=settings.groq_api_key,
                model_name=settings.groq_model_name,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        except Exception:
            logger.warning("Failed to initialize ChatGroq — checking alternatives", exc_info=True)

    # Fallback to Google Gemini if configured
    if settings.google_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            logger.info("Fallback to Google Gemini LLM")
            return ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model=settings.llm_model_name,
                temperature=settings.llm_temperature,
            )
        except Exception:
            pass

    logger.warning("No LLM provider initialized — system operating in deterministic fallback mode")
    return None
