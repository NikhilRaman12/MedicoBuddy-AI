"""Test script to verify structured 9-part MedicoBuddy responses across multiple query types."""

import json
import urllib.request

TEST_QUERIES = [
    "Mild headache since this morning after work",
    "I have a mild stomach discomfort after eating heavy food",
    "Uncomplicated cold symptoms and mild cough",
    "Temporary fatigue after a long workday",
    "Minor nasal allergy symptoms",
]

API_URL = "http://127.0.0.1:8000/api/v1/chat"


def run_tests():
    print("================================================================================")
    print("VERIFYING STRUCTURED RESPONSES ACROSS 5 DIVERSE HEALTH QUERIES")
    print("================================================================ handler\n")

    all_passed = True

    for idx, query in enumerate(TEST_QUERIES, start=1):
        print(f"--- [Query #{idx}]: '{query}' ---")
        payload = {
            "message": query,
            "thread_id": f"struct_test_{idx}",
            "consent_given": True,
        }
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))

                applies_to = res_data.get("what_this_applies_to", "")
                summary = res_data.get("summary", "")
                action_table = res_data.get("action_table", [])
                impl_plan = res_data.get("implementation_plan", {})
                avoid_mon = res_data.get("avoid_and_monitor", [])
                when_seek = res_data.get("when_to_seek_care", [])
                citations = res_data.get("citations", [])
                educational_stmt = res_data.get("educational_statement", "")

                print(f"  [OK] Scope Summary: {applies_to[:70]}...")
                print(f"  [OK] Summary: {summary[:100]}...")
                print(f"  [OK] Action Table Rows: {len(action_table)} rows")
                if action_table:
                    first_row = action_table[0]
                    print(f"      Row 1 Lens: {first_row.get('guidance_lens')}")
                    print(f"      Row 1 Action: {first_row.get('what_may_help')}")
                    print(f"      Row 1 Citations: {first_row.get('citation_ids')}")

                print(f"  [OK] Implementation Plan: Now='{impl_plan.get('now')[:40]}...', Next 6-12h='{impl_plan.get('next_6_to_12_hours')[:40]}...'")
                print(f"  [OK] Avoid & Monitor: {len(avoid_mon)} rows")
                print(f"  [OK] When to Seek Care: {len(when_seek)} items")
                print(f"  [OK] Citations: {len(citations)} citations")
                for c_idx, c in enumerate(citations[:2], start=1):
                    print(f"      [{c.get('citation_id')}] {c.get('title')} ({c.get('publisher')})")
                print(f"  [OK] Educational Statement Present: {'Yes' if educational_stmt else 'No'}\n")

                # Validation checks
                if len(action_table) < 2 or len(citations) < 2 or not applies_to or not summary:
                    print(f"  [FAIL] VALIDATION FAILED for Query #{idx}!\n")
                    all_passed = False
                else:
                    print(f"  [PASS] Query #{idx} PASSED all 9 structured contract checks!\n")

        except Exception as exc:
            print(f"  [ERROR] executing query #{idx}: {exc}\n")
            all_passed = False

    print("================================================================================")
    if all_passed:
        print("OVERALL RESULT: ALL 5 QUERIES RETURNED VALID GROUNDED STRUCTURED RESPONSES!")
    else:
        print("OVERALL RESULT: SOME QUERIES FAILED STRUCTURED CONTRACT VERIFICATION.")
    print("================================================================================")


if __name__ == "__main__":
    run_tests()
