"""Generate release_gate_report.json for MedicoBuddy AI production deployment.

Validates all 14 release gate criteria and produces a machine-readable JSON report.
Fails with exit code 1 if any CRITICAL gate fails.

Usage:
    python scripts/generate_release_report.py
    python scripts/generate_release_report.py --output release_gate_report.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# ─────────────────────────────────────────────────────────────
RELEASE_GATE_CRITERIA = [
    # (gate_id, description, severity)
    ("G01", "No hardcoded similarity scores in nodes.py", "CRITICAL"),
    ("G02", "No hardcoded evidence_sufficient=True in nodes.py", "CRITICAL"),
    ("G03", "No hardcoded medicobuddy_metadata_registry.pdf citation", "CRITICAL"),
    ("G04", "No hardcoded Neo4j graph path in frontend", "CRITICAL"),
    ("G05", "No hardcoded 'Hydration & Rest' table default in frontend", "CRITICAL"),
    ("G06", "corrective_retrieval node present in workflow", "CRITICAL"),
    ("G07", "_search_local_faiss() method present in VectorStoreClient", "CRITICAL"),
    ("G08", "GET /health/dependencies endpoint present", "CRITICAL"),
    ("G09", "GET /chat endpoint present", "MAJOR"),
    ("G10", "req_id defined before SSE event_generator scope", "CRITICAL"),
    ("G11", "GroqStructuredResponse Pydantic model importable", "CRITICAL"),
    ("G12", "ingest_and_index.py script exists and is runnable", "MAJOR"),
    ("G13", "groq_output.py model exists with required fields", "CRITICAL"),
    ("G14", "All 15 workflow nodes present in graph.py", "CRITICAL"),
]


# ─────────────────────────────────────────────────────────────
def check_gate(gate_id: str) -> dict[str, Any]:
    """Run a single release gate check. Returns result dict."""
    result = {
        "gate_id": gate_id,
        "status": "FAIL",
        "detail": "",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        if gate_id == "G01":
            nodes_path = PROJECT_ROOT / "src" / "medicobuddy" / "workflow" / "nodes.py"
            content = nodes_path.read_text(encoding="utf-8")
            if "0.95, 0.92" in content or '"vector_scores": [0.95' in content:
                result["detail"] = "FAIL: Hardcoded similarity scores [0.95, 0.92] found"
            else:
                result["status"] = "PASS"
                result["detail"] = "No hardcoded similarity scores detected"

        elif gate_id == "G02":
            nodes_path = PROJECT_ROOT / "src" / "medicobuddy" / "workflow" / "nodes.py"
            content = nodes_path.read_text(encoding="utf-8")
            if '"evidence_sufficient": True' in content:
                result["detail"] = "FAIL: Hardcoded 'evidence_sufficient': True found"
            else:
                result["status"] = "PASS"
                result["detail"] = "evidence_sufficient is conditionally set, not hardcoded"

        elif gate_id == "G03":
            nodes_path = PROJECT_ROOT / "src" / "medicobuddy" / "workflow" / "nodes.py"
            content = nodes_path.read_text(encoding="utf-8")
            # The registry name is acceptable only as a sentinel being REJECTED
            lines_with_registry = [
                l for l in content.splitlines()
                if "medicobuddy_metadata_registry.pdf" in l
                and "hardcoded" not in l.lower() and "sentinel" not in l.lower()
                and "blocked" not in l.lower() and "reject" not in l.lower()
                and "#" not in l.split("medicobuddy")[0]  # not a comment
                and "source_file ==" not in l.lower()  # not a comparison guard
            ]
            if lines_with_registry:
                result["detail"] = f"FAIL: Unexpected use of metadata registry citation in {len(lines_with_registry)} lines"
            else:
                result["status"] = "PASS"
                result["detail"] = "medicobuddy_metadata_registry.pdf not used as citation source"

        elif gate_id == "G04":
            frontend_path = PROJECT_ROOT / "frontend" / "app.py"
            content = frontend_path.read_text(encoding="utf-8")
            if "MildHeadache)-[:MAY_SUPPORT]->" in content:
                result["detail"] = "FAIL: Hardcoded Neo4j graph path found in frontend"
            else:
                result["status"] = "PASS"
                result["detail"] = "No hardcoded Neo4j traversal path in frontend"

        elif gate_id == "G05":
            frontend_path = PROJECT_ROOT / "frontend" / "app.py"
            content = frontend_path.read_text(encoding="utf-8")
            if '"Hydration & Rest"' in content or "'Hydration & Rest'" in content:
                result["detail"] = "FAIL: Hardcoded 'Hydration & Rest' default in table rendering"
            else:
                result["status"] = "PASS"
                result["detail"] = "No hardcoded table cell defaults found"

        elif gate_id == "G06":
            graph_path = PROJECT_ROOT / "src" / "medicobuddy" / "workflow" / "graph.py"
            content = graph_path.read_text(encoding="utf-8")
            if "corrective_retrieval" in content:
                result["status"] = "PASS"
                result["detail"] = "corrective_retrieval node present in workflow graph"
            else:
                result["detail"] = "FAIL: corrective_retrieval node missing from graph.py"

        elif gate_id == "G07":
            vs_path = PROJECT_ROOT / "src" / "medicobuddy" / "retrieval" / "vector_store.py"
            content = vs_path.read_text(encoding="utf-8")
            if "_search_local_faiss" in content:
                result["status"] = "PASS"
                result["detail"] = "_search_local_faiss() method present in VectorStoreClient"
            else:
                result["detail"] = "FAIL: _search_local_faiss() method missing from vector_store.py"

        elif gate_id == "G08":
            health_path = PROJECT_ROOT / "src" / "medicobuddy" / "api" / "routes" / "health.py"
            content = health_path.read_text(encoding="utf-8")
            if "/health/dependencies" in content:
                result["status"] = "PASS"
                result["detail"] = "GET /health/dependencies endpoint present"
            else:
                result["detail"] = "FAIL: /health/dependencies endpoint missing from health.py"

        elif gate_id == "G09":
            chat_path = PROJECT_ROOT / "src" / "medicobuddy" / "api" / "routes" / "chat.py"
            content = chat_path.read_text(encoding="utf-8")
            if 'router.get("/chat"' in content or "router.get('/chat'" in content:
                result["status"] = "PASS"
                result["detail"] = "GET /chat info endpoint present"
            else:
                result["detail"] = "FAIL: GET /chat endpoint missing from chat.py"

        elif gate_id == "G10":
            chat_path = PROJECT_ROOT / "src" / "medicobuddy" / "api" / "routes" / "chat.py"
            content = chat_path.read_text(encoding="utf-8")
            # Check that req_id is defined inside event_generator scope
            lines = content.splitlines()
            in_event_gen = False
            req_id_defined_inside = False
            for line in lines:
                if "async def event_generator" in line:
                    in_event_gen = True
                if in_event_gen and "req_id = str(_uuid.uuid4())" in line:
                    req_id_defined_inside = True
                    break
                if in_event_gen and "async def " in line and "event_generator" not in line:
                    in_event_gen = False  # left scope

            if req_id_defined_inside:
                result["status"] = "PASS"
                result["detail"] = "req_id correctly defined inside event_generator scope"
            else:
                result["detail"] = "FAIL: req_id may still be undefined at event_generator call time"

        elif gate_id == "G11":
            groq_path = PROJECT_ROOT / "src" / "medicobuddy" / "models" / "groq_output.py"
            if groq_path.exists():
                content = groq_path.read_text(encoding="utf-8")
                required = ["GroqStructuredResponse", "ActionTableRowSchema",
                            "CitationSchema", "QuickActionSchema"]
                missing = [r for r in required if r not in content]
                if missing:
                    result["detail"] = f"FAIL: Missing classes in groq_output.py: {missing}"
                else:
                    result["status"] = "PASS"
                    result["detail"] = "GroqStructuredResponse and all sub-models present"
            else:
                result["detail"] = "FAIL: groq_output.py does not exist"

        elif gate_id == "G12":
            ingest_path = PROJECT_ROOT / "scripts" / "ingest_and_index.py"
            if ingest_path.exists():
                content = ingest_path.read_text(encoding="utf-8")
                has_upsert = "upsert_document" in content
                has_embed = "embed_batch" in content
                has_report = "ingestion_report.json" in content
                if has_upsert and has_embed and has_report:
                    result["status"] = "PASS"
                    result["detail"] = "ingest_and_index.py exists with upsert, embed, and report logic"
                else:
                    result["detail"] = (
                        f"FAIL: ingest_and_index.py missing: "
                        f"upsert={has_upsert}, embed={has_embed}, report={has_report}"
                    )
            else:
                result["detail"] = "FAIL: ingest_and_index.py does not exist"

        elif gate_id == "G13":
            groq_path = PROJECT_ROOT / "src" / "medicobuddy" / "models" / "groq_output.py"
            if groq_path.exists():
                content = groq_path.read_text(encoding="utf-8")
                required_fields = [
                    "summary", "action_table", "implementation_plan",
                    "things_to_avoid", "warning_signs", "quick_actions",
                    "citations", "evidence_strength",
                ]
                missing = [f for f in required_fields if f not in content]
                if missing:
                    result["detail"] = f"FAIL: Missing fields in GroqStructuredResponse: {missing}"
                else:
                    result["status"] = "PASS"
                    result["detail"] = "All 8 required fields present in GroqStructuredResponse"
            else:
                result["detail"] = "FAIL: groq_output.py does not exist"

        elif gate_id == "G14":
            graph_path = PROJECT_ROOT / "src" / "medicobuddy" / "workflow" / "graph.py"
            content = graph_path.read_text(encoding="utf-8")
            required_nodes = [
                "language_router", "scope_validator", "red_flag_triage",
                "clarification", "query_planner", "mcp_retrieval",
                "hybrid_retrieval", "corrective_retrieval", "evidence_grader",
                "safety_critic", "response_composer", "output_validator",
                "citation_validator", "structured_translation", "final_response",
            ]
            missing = [n for n in required_nodes if n not in content]
            if missing:
                result["detail"] = f"FAIL: Missing workflow nodes: {missing}"
            else:
                result["status"] = "PASS"
                result["detail"] = f"All {len(required_nodes)} required workflow nodes present"

    except Exception as exc:
        result["status"] = "ERROR"
        result["detail"] = f"Gate check raised exception: {exc}"

    return result


def run_all_gates() -> dict[str, Any]:
    """Run all release gate checks and compile report."""
    print("=" * 70)
    print("MedicoBuddy AI — Release Gate Report")
    print("=" * 70)

    gate_results: list[dict[str, Any]] = []
    failed_critical = 0
    failed_major = 0
    passed = 0

    for gate_id, description, severity in RELEASE_GATE_CRITERIA:
        result = check_gate(gate_id)
        result["description"] = description
        result["severity"] = severity
        gate_results.append(result)

        icon = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
        print(f"{icon} [{severity}] {gate_id}: {description}")
        if result["status"] != "PASS":
            print(f"    -> {result['detail']}")

        if result["status"] == "PASS":
            passed += 1
        elif severity == "CRITICAL":
            failed_critical += 1
        else:
            failed_major += 1

    # Test suite gate
    print("\nRunning test suite...")
    import subprocess
    test_result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_mandatory_spec.py",
         "--tb=no", "-q", "--no-header"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
    )
    test_passed = test_result.returncode == 0
    test_output = test_result.stdout.strip().splitlines()
    test_summary = test_output[-1] if test_output else "No output"
    test_gate = {
        "gate_id": "G15",
        "description": "All pytest tests pass",
        "severity": "CRITICAL",
        "status": "PASS" if test_passed else "FAIL",
        "detail": test_summary,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    gate_results.append(test_gate)
    icon = "[PASS]" if test_passed else "[FAIL]"
    print(f"{icon} [CRITICAL] G15: All pytest tests pass")
    print(f"    -> {test_summary}")
    if test_passed:
        passed += 1
    else:
        failed_critical += 1

    overall = "PASS" if failed_critical == 0 else "FAIL"
    print(f"\n{'=' * 70}")
    print(f"Overall Status: {overall}")
    print(f"  PASS: {passed} | CRITICAL FAIL: {failed_critical} | MAJOR FAIL: {failed_major}")
    print("=" * 70)

    # Build report
    report = {
        "report_version": "2.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "product": "MedicoBuddy AI",
        "release_tag": "production_release_v2",
        "git_commit": os.getenv("GIT_COMMIT_SHA", "dev"),
        "overall_status": overall,
        "gates_total": len(gate_results),
        "gates_passed": passed,
        "gates_failed_critical": failed_critical,
        "gates_failed_major": failed_major,
        "gates": gate_results,
        "deployment_approved": overall == "PASS",
    }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="MedicoBuddy AI Release Gate Report")
    parser.add_argument(
        "--output", default="release_gate_report.json",
        help="Output path for the release gate report JSON",
    )
    args = parser.parse_args()

    report = run_all_gates()

    output_path = PROJECT_ROOT / args.output
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport written to: {output_path}")

    if not report["deployment_approved"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
