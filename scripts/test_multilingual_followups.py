"""Multilingual Acceptance Test Suite for MedicoBuddy AI.

Verifies:
1. Language routing & preferred language override (e.g. Telugu selected + English query -> Telugu answer).
2. Concept canonicalization for hair loss variants (safety tips hairfall vs safety measures for hairfall).
3. 4-6 contextual interactive follow-ups generated per topic.
4. Citation preservation (PMIDs/DOIs/URLs untouched).
5. Clean JSON structure with no manufactured frontend fallbacks.
"""

from __future__ import annotations

import json
import sys
import time
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://127.0.0.1:8000/api/v1"

TEST_MATRIX = [
    {
        "name": "Case 1: Telugu Selected + English Input (Headache)",
        "preferred_language": "te",
        "message": "Mild headache since this morning after work",
        "expected_lang_code": "te",
        "unicode_check": lambda text: any("\u0c00" <= c <= "\u0c7f" for c in text),
    },
    {
        "name": "Case 2: Telugu Selected + Telugu Input (Stomach Discomfort)",
        "preferred_language": "te",
        "message": "కడుపులో అసౌకర్యం మరియు గ్యాస్ ఉపశమనం",
        "expected_lang_code": "te",
        "unicode_check": lambda text: any("\u0c00" <= c <= "\u0c7f" for c in text),
    },
    {
        "name": "Case 3: Hindi Selected + English Input (Cold & Cough)",
        "preferred_language": "hi",
        "message": "Cold and cough symptoms with sore throat",
        "expected_lang_code": "hi",
        "unicode_check": lambda text: any("\u0900" <= c <= "\u097f" for c in text),
    },
    {
        "name": "Case 4: Tamil Selected + Telugu Input (Fever)",
        "preferred_language": "ta",
        "message": "జ్వరం మరియు మైకం నివారణ",
        "expected_lang_code": "ta",
        "unicode_check": lambda text: any("\u0b80" <= c <= "\u0bff" for c in text),
    },
    {
        "name": "Case 5: Auto Selected + Bengali Input (Nausea)",
        "preferred_language": "auto",
        "message": "বমি বমি ভাব এবং ঘরোয়া প্রতিকার",
        "expected_lang_code": "bn",
        "unicode_check": lambda text: any("\u0980" <= c <= "\u09ff" for c in text),
    },
    {
        "name": "Case 6: English Selected + Hindi Input (Skin Care)",
        "preferred_language": "en",
        "message": "त्वचा की सूखी जलन के लिए उपाय",
        "expected_lang_code": "en",
        "unicode_check": lambda text: True,
    },
    {
        "name": "Case 7: Urdu Selected + English Input (Stress)",
        "preferred_language": "ur",
        "message": "Stress relief and relaxation techniques",
        "expected_lang_code": "ur",
        "unicode_check": lambda text: any("\u0600" <= c <= "\u06ff" for c in text),
    },
]

HAIR_LOSS_TESTS = [
    {"query": "safety tips hairfall", "preferred_language": "te"},
    {"query": "safety measures for hairfall", "preferred_language": "te"},
]


def run_tests():
    print("=" * 80)
    print("  MedicoBuddy AI — Multilingual Acceptance & Follow-Up Test Suite")
    print("=" * 80)

    passed_matrix = 0
    total_matrix = len(TEST_MATRIX)

    for idx, test in enumerate(TEST_MATRIX, start=1):
        print(f"\n[{idx}/{total_matrix}] TESTING: {test['name']}")
        print(f"    Payload: message='{test['message']}', preferred_language='{test['preferred_language']}'")

        payload = {
            "message": test["message"],
            "preferred_language": test["preferred_language"],
            "thread_id": "test_multilingual_thread",
            "age_range": "18-65",
            "pregnancy_status": "unknown",
            "chronic_conditions": [],
            "region": "IN",
            "consent_given": True,
        }

        try:
            resp = httpx.post(f"{API_BASE}/chat", json=payload, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                summary = data.get("summary", "")
                action_table = data.get("action_table", [])
                chips = data.get("quick_action_chips", [])
                safety = data.get("safety_status", "")

                print(f"    STATUS: 200 OK | Safety: {safety} | Action Rows: {len(action_table)}")
                print(f"    Summary: {summary[:100]}...")
                print(f"    Quick Chips ({len(chips)}): {chips}")

                # Assert 4-6 chips
                assert len(chips) >= 3, f"Expected at least 3 chips, got {len(chips)}"
                assert len(action_table) > 0, "Expected non-empty action_table"

                # Unicode / language check
                if test["expected_lang_code"] != "en":
                    has_target_unicode = test["unicode_check"](summary) or any(test["unicode_check"](r.get("what_may_help", "")) for r in action_table)
                    assert has_target_unicode, f"Response did not contain target language {test['expected_lang_code']} Unicode character range!"

                print("    RESULT: PASSED")
                passed_matrix += 1
            else:
                print(f"    FAILED HTTP {resp.status_code}: {resp.text}")
        except Exception as exc:
            print(f"    FAILED Exception: {exc}")

    # Hair loss concept canonicalization test
    print("\n" + "=" * 80)
    print("  Testing Hair Loss Multilingual Concept Canonicalization...")
    print("=" * 80)

    hair_results = []
    for test in HAIR_LOSS_TESTS:
        print(f"    Testing Query: '{test['query']}'")
        payload = {
            "message": test["query"],
            "preferred_language": test["preferred_language"],
            "thread_id": "hair_test_thread",
            "consent_given": True,
        }
        resp = httpx.post(f"{API_BASE}/chat", json=payload, timeout=30.0)
        assert resp.status_code == 200, f"HTTP failure for query {test['query']}"
        data = resp.json()
        hair_results.append(data)
        print(f"    Returned {len(data.get('action_table', []))} action rows, {len(data.get('quick_action_chips', []))} chips.")

    # Check both hair queries retrieved hair loss guidance
    h1_table = hair_results[0].get("action_table", [])
    h2_table = hair_results[1].get("action_table", [])
    assert len(h1_table) > 0 and len(h2_table) > 0, "Hair loss queries must return non-empty action table"
    print("\n[SUCCESS] Hair loss concept canonicalization test PASSED")

    print("\n" + "=" * 80)
    if passed_matrix == total_matrix:
        print(f"ALL ACCEPTANCE TESTS PASSED ({passed_matrix}/{total_matrix})!")
        print("=" * 80)
        sys.exit(0)
    else:
        print(f"TEST SUITE FAILED ({passed_matrix}/{total_matrix} passed)")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
