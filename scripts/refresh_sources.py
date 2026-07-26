"""Incremental evidence source refresh script for MedicoBuddy AI.

Verifies source freshness, checks retraction status, and updates indexes idempotently.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from scripts.ingest_sources import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("refresh_sources")


def refresh_sources() -> None:
    """Run incremental source refresh."""
    logger.info("Starting evidence refresh job at %s", datetime.now(timezone.utc).isoformat())
    report = run_ingestion()
    logger.info("Refresh completed with status: %s", report.get("status"))


if __name__ == "__main__":
    refresh_sources()
