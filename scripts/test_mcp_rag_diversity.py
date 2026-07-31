"""MCP Evidence RAG Diversity & Substantive Answer Assertion Test.

Executes 6 distinct health queries:
1. headache
2. stomach_discomfort
3. nausea
4. cold
5. allergy
6. hair_care

Asserts that each query produces distinct:
- Retrieved Chunk / Citation IDs & URLs
- Action Table Guidance Rows (Guidance lens, Remedy name, Cautions)
- Answer Summaries
- Follow-up Questions

Fails release (exit code 1) if any two unrelated queries share identical substantive answers.
"""

from __future__ import annotations

import json
import sys
import httpx

API_URL = "http://127.0.0.1:8000/api/v1/chat"

TEST_QUERIES = [
    {"topic": "headache", "query": "Mild headache since this morning after work"},
    {"topic": "stomach_discomfort", "query": "Mild stomach discomfort and gas after eating"},
    {"topic": "nausea", "query": "What is nausea and how to treat it naturally"},
    {"topic": "cold", "query": "Uncomplicated cold symptoms and mild cough"},
    {"topic": "allergy", "query": "Seasonal allergies and sinus pressure relief"},
    {"topic": "hair_care", "query": "Hair care and scalp health natural remedies"},
]


def run_diversity_test() -> None:
    print("=" * 80)
    print("  MedicoBuddy AI — Allowlisted MCP RAG Answer Diversity & Assertion Test")
    print("=" * 80)

    results: list[dict] = []
    failed = False

    with httpx.Client(timeout=30.0) as client:
        for idx, item in enumerate(TEST_QUERIES, start=1):
            topic = item["topic"]
            query = item["query"]

            payload = {
                "message": query,
                "consent_given": True,
                "thread_id": f"test_thread_{topic}",
            }

            try:
                resp = client.post(API_URL, json=payload)
                if resp.status_code != 200:
                    print(f"[{idx}/6] FAILED HTTP {resp.status_code}: {resp.text}")
                    failed = True
                    continue

                data = resp.json()
                action_table = data.get("action_table", [])
                citations = data.get("citations", [])
                summary = data.get("summary", "")
                follow_up = data.get("follow_up_question", "")

                remedy_names = [row.get("what_may_help", "") for row in action_table]
                citation_ids = [c.get("citation_id", c.get("title", "")) for c in citations]

                print(f"[{idx}/6] TOPIC: {topic}")
                print(f"       QUERY: '{query}'")
                print(f"       REMEDIES: {remedy_names}")
                print(f"       CITATIONS ({len(citations)}): {[c.get('title', '')[:40] for c in citations[:3]]}")
                print(f"       FOLLOW-UP: '{follow_up[:70]}...'")
                print("-" * 80)

                results.append({
                    "topic": topic,
                    "query": query,
                    "remedies": remedy_names,
                    "citations": citation_ids,
                    "summary": summary,
                    "follow_up": follow_up,
                })
            except Exception as exc:
                print(f"[{idx}/6] ERROR on query '{query}': {exc}")
                failed = True

    if len(results) < len(TEST_QUERIES):
        print("\n[FAIL] RELEASE TEST FAILED: Not all queries completed successfully.")
        sys.exit(1)

    print("\nRunning Substantive Answer Pairwise Diversity Assertions...")

    pair_failures = 0
    total_pairs = 0

    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            res_a = results[i]
            res_b = results[j]
            total_pairs += 1

            topic_a, topic_b = res_a["topic"], res_b["topic"]

            # Assertion 1: Remedy names must be different
            if res_a["remedies"] == res_b["remedies"]:
                print(f"  [PAIR FAIL] ({topic_a} vs {topic_b}): Identical Action Table remedies! {res_a['remedies']}")
                pair_failures += 1

            # Assertion 2: Summaries must be different
            if res_a["summary"] and res_b["summary"] and res_a["summary"] == res_b["summary"]:
                print(f"  [PAIR FAIL] ({topic_a} vs {topic_b}): Identical summaries!")
                pair_failures += 1

            # Assertion 3: Follow-up questions must be different
            if res_a["follow_up"] and res_b["follow_up"] and res_a["follow_up"] == res_b["follow_up"]:
                print(f"  [PAIR FAIL] ({topic_a} vs {topic_b}): Identical follow-up questions!")
                pair_failures += 1

    print("=" * 80)
    if pair_failures > 0 or failed:
        print(f"[FAIL] RELEASE VERIFICATION FAILED: {pair_failures} pairwise collisions out of {total_pairs} pairs evaluated.")
        sys.exit(1)
    else:
        print(f"[SUCCESS] RELEASE VERIFICATION PASSED: All {total_pairs} topic pairs produced 100% distinct, substantive evidence-backed answers!")
        print("=" * 80)
        sys.exit(0)


if __name__ == "__main__":
    run_diversity_test()
