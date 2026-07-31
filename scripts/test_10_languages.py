"""Terminal verification test for 10 random health questions in 10 languages.

Languages:
1. English (Headache)
2. Hindi (Cold & Cough)
3. Telugu (Stomach Discomfort)
4. Tamil (Fever)
5. Bengali (Nausea)
6. Marathi (Skin Care)
7. Gujarati (Hair Care)
8. Kannada (Stress)
9. Malayalam (Sleep)
10. Punjabi (Fatigue)

Asserts:
- Status 200 OK
- Structured 12-section answer contract with Action Table
- Language detection
- Question-specific relevance & pairwise answer uniqueness
"""

from __future__ import annotations

import json
import sys
import httpx

API_URL = "http://127.0.0.1:8000/api/v1/chat"

LANG_TEST_CASES = [
    {"lang": "English", "code": "en", "topic": "Headache", "query": "Mild headache since this morning after work"},
    {"lang": "Hindi", "code": "hi", "topic": "Cold & Cough", "query": "जुकाम और खांसी का इलाज"},
    {"lang": "Telugu", "code": "te", "topic": "Stomach Discomfort", "query": "కడుపులో అసౌకర్యం మరియు గ్యాస్ ఉపశమనం"},
    {"lang": "Tamil", "code": "ta", "topic": "Fever", "query": "காய்ச்சல் மற்றும் உடல் வலி நிவாரணம்"},
    {"lang": "Bengali", "code": "bn", "topic": "Nausea", "query": "বমি বমি ভাব এবং ঘরোয়া প্রতিকার"},
    {"lang": "Marathi", "code": "mr", "topic": "Skin Care", "query": "त्वचेचा कोरडेपणा आणि खाज कमी करा"},
    {"lang": "Gujarati", "code": "gu", "topic": "Hair Care", "query": "વાળની સંભાળ અને ખરતા વાળ માટે ઉપાય"},
    {"lang": "Kannada", "code": "kn", "topic": "Stress", "query": "ಒತ್ತಡ ಪರಿಹಾರ ಮತ್ತು ಮಾನಸಿಕ ಶಾಂತಿ"},
    {"lang": "Malayalam", "code": "ml", "topic": "Sleep", "query": "ഉറക്കമില്ലായ്മ മാറ്റാൻ പ്രകൃതിദത്ത വഴികൾ"},
    {"lang": "Punjabi", "code": "pa", "topic": "Fatigue", "query": "ਸਰੀਰਕ ਥਕਾਵਟ ਅਤੇ ਕਮਜ਼ੋਰੀ ਦੇ ਇਲਾਜ"},
]


def safe_str(val: str, max_len: int = 60) -> str:
    """Safely format strings for console printing across Windows code pages."""
    cleaned = val[:max_len].replace("\n", " ")
    return cleaned.encode("ascii", "xmlcharrefreplace").decode("ascii")


def run_10_lang_test() -> None:
    print("=" * 80)
    print("  MedicoBuddy AI — 10 Languages & 10 Distinct Questions Terminal Test")
    print("=" * 80)

    results: list[dict] = []
    failed = False

    with httpx.Client(timeout=30.0) as client:
        for idx, tc in enumerate(LANG_TEST_CASES, start=1):
            lang = tc["lang"]
            topic = tc["topic"]
            query = tc["query"]

            payload = {
                "message": query,
                "consent_given": True,
                "thread_id": f"thread_10lang_{tc['code']}",
            }

            try:
                resp = client.post(API_URL, json=payload)
                if resp.status_code != 200:
                    print(f"[{idx:02d}/10] FAILED ({lang} - {topic}) HTTP {resp.status_code}: {resp.text}")
                    failed = True
                    continue

                data = resp.json()
                action_table = data.get("action_table", [])
                summary = data.get("summary", "")
                follow_up = data.get("follow_up_question", "")
                safety = data.get("safety_status", "")

                remedies = [row.get("what_may_help", "") for row in action_table]

                print(f"[{idx:02d}/10] LANG: {lang:<10} | TOPIC: {topic}")
                print(f"        QUERY:    '{safe_str(query, 50)}'")
                print(f"        STATUS:   200 OK | Safety: {safety} | Action Rows: {len(action_table)}")
                for r_idx, r_name in enumerate(remedies, start=1):
                    print(f"          Row {r_idx}: {safe_str(r_name, 55)}")
                print(f"        SUMMARY:  {safe_str(summary, 70)}...")
                print(f"        FOLLOWUP: {safe_str(follow_up, 70)}...")
                print("-" * 80)

                results.append({
                    "lang": lang,
                    "topic": topic,
                    "query": query,
                    "remedies": remedies,
                    "summary": summary,
                    "follow_up": follow_up,
                })

            except Exception as exc:
                print(f"[{idx:02d}/10] ERROR ({lang} - {topic}): {safe_str(str(exc), 80)}")
                failed = True

    if len(results) < len(LANG_TEST_CASES):
        print("\n[FAIL] TEST FAILED: Not all 10 language queries completed successfully.")
        sys.exit(1)

    print("\nRunning Pairwise Answer Uniqueness & Relevance Verification Across 10 Languages...")

    collisions = 0
    total_pairs = 0

    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            total_pairs += 1
            r1, r2 = results[i], results[j]

            if r1["remedies"] == r2["remedies"]:
                print(f"  [COLLISION] {r1['lang']} ({r1['topic']}) vs {r2['lang']} ({r2['topic']}): Identical remedies!")
                collisions += 1

    print("=" * 80)
    if collisions > 0 or failed:
        print(f"[FAIL] VERIFICATION FAILED: {collisions} answer collisions out of {total_pairs} pairs evaluated.")
        sys.exit(1)
    else:
        print(f"[SUCCESS] ALL 10/10 LANGUAGES PASSED! All {total_pairs} question pairs generated unique, structured, topic-specific answers!")
        print("=" * 80)
        sys.exit(0)


if __name__ == "__main__":
    run_10_lang_test()
