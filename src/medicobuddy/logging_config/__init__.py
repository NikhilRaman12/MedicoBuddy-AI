"""Structured logging configuration with OpenTelemetry compatibility and PII redaction."""

from __future__ import annotations

import logging
import logging.config
from typing import Any

from medicobuddy.privacy.pii_redactor import redact_pii


class PIIRedactingFilter(logging.Filter):
    """Logging filter that redacts PII from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_pii(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_pii(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_pii(str(a)) if isinstance(a, str) else a for a in record.args
                )
        return True


LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "pii_redact": {
            "()": PIIRedactingFilter,
        },
    },
    "formatters": {
        "structured": {
            "format": (
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s", '
                '"module": "%(module)s", "function": "%(funcName)s"}'
            ),
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "structured",
            "filters": ["pii_redact"],
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "medicobuddy": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}


def setup_logging() -> None:
    """Initialize structured logging with PII redaction."""
    logging.config.dictConfig(LOGGING_CONFIG)
