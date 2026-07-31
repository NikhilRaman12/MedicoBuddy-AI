"""Terminal verification script for testing 20 random health queries with MedicoBuddy GraphRAG.

Executes 20 varied queries against the API endpoint, verifies RAG retrieval,
Action Table structured rows generation, safety status, and prints clean terminal output.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_20_queries")

API_URL = "http://127.0.0.1:8000/api/v1/chat"

TEST_20_QUERIES = [
    {"id": 1, "topic": "Headache", "query": "Mild headache since this morning after work"},
    {"id": 2, "topic": "Cold & Cough", "query": "Uncomplicated cold symptoms and mild cough"},
    {"id": 3, "topic": "Digestive", "query": "Mild stomach discomfort after eating"},
    {"id": 4, "topic": "Nausea", "query": "What is nausea and how to treat it naturally"},
    {"id": 5, "topic": "Allergies", "query": "Seasonal allergies and sinus pressure relief"},
    {"id": 6, "topic": "Fatigue", "query": "Temporary fatigue and low energy after long day"},
    {"id": 7, "topic": "Fever", "query": "Mild fever and body aches guidelines"},
    {"id": 8, "topic": "Sleep", "query": "Insomnia and sleep hygiene natural remedies"},
    {"id": 9, "topic": "Skin Care", "query": "Mild skin dryness and irritation relief"},
    {"id": 10, "topic": "Hair Care", "query": "Hair care and scalp health natural remedies"},
    {"id": 11, "topic": "Stress", "query": "Stress management and anxiety relief tips"},
    {"id": 12, "topic": "Bloating", "query": "Bloating and gas relief after meals"},
    {"id": 13, "topic": "Constipation", "query": "Mild constipation natural remedies"},
    {"id": 14, "topic": "Sore Throat", "query": "Sore throat and scratchy throat remedies"},
    {"id": 15, "topic": "Dizziness", "query": "Dizziness or lightheadedness when standing up"},
    {"id": 16, "topic": "Ayurvedic Digestion", "query": "Ayurvedic remedies for digestive fire and indigestion"},
    {"id": 17, "topic": "Immune Boosting", "query": "Natural immune boosting suggestions for seasonal change"},
    {"id": 18, "topic": "Hindi Query", "query": "हल्का सिरदर्द और काम के बाद थकान"},
    {"id": 19, "topic": "Telugu Query", "query": "ఉదయం నుండి తేలికపాటి తలనొప్పి"},
    {"id": 20, "topic": "Tamil Query", "query": "காய்ச்சல் மற்றும் இருமல் நிவாரணம்"},
]


async def run_20_query_test() -> None:
    print("=" * 80)
    print("  MedicoBuddy GraphRAG — 20 Query Terminal Verification Test")
    print("=" * 80)
    print()

    passed_count = 0
    failed_count = 0
    total_action_rows = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        for item in TEST_20_QUERIES:
            q_id = item["id"]
            topic = item["topic"]
            query = item["query"]

            t0 = time.monotonic()
            payload = {
                "message": query,
                "thread_id": f"test_20_{q_id}",
                "age_range": "18-65",
                "pregnancy_status": "unknown",
                "chronic_conditions": [],
                "region": "IN",
                "consent_given": True,
            }

            try:
                resp = await client.post(API_URL, json=payload)
                latency = (time.monotonic() - t0) * 1000.0

                if resp.status_code == 200:
                    data = resp.json()
                    safety = data.get("safety_status", "unknown").upper()
                    action_table = data.get("action_table", [])
                    summary = data.get("summary", "")[:120].replace("\n", " ")
                    dbg = data.get("debug_panel", {})
                    retrieved_chunks = dbg.get("retrieved_chunks", 0)

                    passed = len(action_table) > 0 and safety != "INSUFFICIENT EVIDENCE"
                    if passed:
                        passed_count += 1
                        total_action_rows += len(action_table)
                    else:
                        failed_count += 1

                    print(f"[{q_id:02d}/20] TOPIC: {topic}")
                    print(f"       QUERY: '{query.encode('ascii', 'xmlcharrefreplace').decode('ascii')}'")
                    print(f"       STATUS: {resp.status_code} OK | Safety: {safety} | Latency: {latency:.1f}ms")
                    print(f"       RETRIEVED CHUNKS: {retrieved_chunks} | ACTION ROWS: {len(action_table)}")

                    for idx, row in enumerate(action_table, start=1):
                        lens = row.get("guidance_lens", "")
                        help_item = row.get("what_may_help", "")
                        ev_str = row.get("evidence_strength", row.get("evidence_level", ""))
                        print(f"         Row {idx}: [{lens}] {help_item} (Evidence: {ev_str})")

                    print(f"       SUMMARY: {summary[:100].encode('ascii', 'xmlcharrefreplace').decode('ascii')}...")
                    print("-" * 80)
                else:
                    failed_count += 1
                    print(f"[{q_id:02d}/20] FAILED ({resp.status_code}): {resp.text}")
                    print("-" * 80)

            except Exception as exc:
                failed_count += 1
                print(f"[{q_id:02d}/20] ERROR: {str(exc).encode('ascii', 'xmlcharrefreplace').decode('ascii')}")
                print("-" * 80)

    print()
    print("=" * 80)
    print(f"  VERIFICATION RESULTS: {passed_count}/20 PASSED ({total_action_rows} total Action Table rows generated)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_20_query_test())
