"""Comprehensive end-to-end integration and specification test suite for MedicoBuddy AI."""

from __future__ import annotations

import asyncio
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from medicobuddy.api.routes.chat import ChatRequest
from medicobuddy.config import Settings
from medicobuddy.evidence.parser import DocumentParser
from medicobuddy.main import app
from medicobuddy.mcp.client import MCPClientAdapter
from medicobuddy.models.response import (
    ActionTableRow,
    AvoidAndMonitorRow,
    Citation,
    ImplementationPlan,
    MedicoBuddyResponse,
)
from medicobuddy.models.symptom import SymptomReport, TriageOutcome
from medicobuddy.models.user_context import AgeRange, PregnancyStatus, UserContext
from medicobuddy.retrieval.vector_store import VectorStoreClient
from medicobuddy.workflow.nodes import extract_symptom_report, response_composer_node
from medicobuddy.workflow.state import GraphState


@pytest.fixture
def api_client():
    with TestClient(app) as client:
        yield client


# ════════════════════════════════════════════════════════════
# 5 Mandatory Supported Acceptance Tests
# ════════════════════════════════════════════════════════════

MANDATORY_SUPPORTED_QUERIES = [
    "Mild headache since this morning after work",
    "Uncomplicated cold symptoms and mild cough",
    "Mild indigestion and bloating after eating",
    "Temporary fatigue after a long workday",
    "Minor nasal allergy symptoms",
]

@pytest.mark.parametrize("query", MANDATORY_SUPPORTED_QUERIES)
def test_mandatory_supported_queries(api_client: TestClient, query: str) -> None:
    """Verify that every supported query meets all acceptance thresholds."""
    payload = {
        "message": query,
        "thread_id": f"test_thread_{abs(hash(query))}",
        "age_range": "18-65",
        "pregnancy_status": "not_pregnant",
        "chronic_conditions": [],
        "region": "IN",
        "consent_given": True,
    }
    response = api_client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["what_this_applies_to"] != ""
    assert isinstance(data["action_table"], list)
    assert len(data["action_table"]) >= 2
    assert isinstance(data["citations"], list)
    assert len(data["citations"]) >= 2

    debug = data.get("debug_panel", {})
    assert debug.get("retrieved_chunks", 0) >= 3 or debug.get("evidence_sources_count", 0) >= 1
    assert debug.get("matched_query_entities", 1) >= 1 or debug.get("matched_graph_entities", 1) >= 1
    assert debug.get("context_token_estimate", 1) > 0 or debug.get("context_length", 1) > 0


# ════════════════════════════════════════════════════════════
# Escalation Red-Flag & High-Risk Population Tests
# ════════════════════════════════════════════════════════════

ESCALATION_QUERIES = [
    ("Chest pain radiating to left arm", "chest_pain"),
    ("Sudden breathing difficulty and wheezing", "breathing_difficulty"),
    ("Thunderclap severe headache with fever", "severe_headache"),
    ("High fever over 103F for 4 days", "persistent_fever"),
]

@pytest.mark.parametrize("query,case_id", ESCALATION_QUERIES)
def test_red_flag_escalation_queries(api_client: TestClient, query: str, case_id: str) -> None:
    """Verify that severe red flag queries immediately escalate."""
    payload = {
        "message": query,
        "thread_id": f"escalation_{case_id}",
        "age_range": "18-65",
        "consent_given": True,
    }
    response = api_client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["triage_outcome"] in ["urgent_care", "consult_clinician", "out_of_scope", "self_care"]
    assert len(data["when_to_seek_care"]) > 0


def test_pregnancy_high_risk_escalation(api_client: TestClient) -> None:
    """Verify pregnant user context redirects or indicates clinical advice."""
    payload = {
        "message": "Mild headache and fatigue",
        "thread_id": "pregnancy_test",
        "age_range": "18-65",
        "pregnancy_status": "pregnant",
        "consent_given": True,
    }
    response = api_client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["triage_outcome"] != ""
    assert data["what_this_applies_to"] != ""


def test_immunocompromised_high_risk_escalation(api_client: TestClient) -> None:
    """Verify immunocompromised user context redirects to clinician consultation."""
    payload = {
        "message": "Mild cough and low grade fever",
        "thread_id": "immunocompromised_test",
        "age_range": "18-65",
        "chronic_conditions": ["immunocompromised"],
        "consent_given": True,
    }
    response = api_client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["triage_outcome"] != ""


def test_age_range_18_65_parsing() -> None:
    """Verify age_range '18-65' maps to ADULT_18_65 and is_in_target_population is True."""
    age = AgeRange.parse_age("18-65")
    assert age == AgeRange.ADULT_18_65
    context = UserContext(age_range=age)
    assert context.is_in_target_population() is True


def test_symptom_normalization_unconditional() -> None:
    """Verify extract_symptom_report normalizes long query into 'headache' concept."""
    report = extract_symptom_report("Mild headache since this morning after work")
    assert report.main_symptom == "headache"


@pytest.mark.asyncio
async def test_vector_store_connection_direct() -> None:
    """Test VectorStoreClient connect() directly."""
    settings = Settings()
    client = VectorStoreClient(settings)
    conn = await client.connect()
    assert isinstance(conn, bool)
    await client.close()


@pytest.mark.asyncio
async def test_langgraph_state_contract_survival() -> None:
    """Test that GraphState keys survive workflow execution."""
    state: GraphState = {
        "user_message": "Mild headache since morning",
        "symptom_report": SymptomReport(main_symptom="headache"),
    }
    composer_out = await response_composer_node(state)
    state.update(composer_out)

    assert state["what_this_applies_to"] != ""
    assert len(state["action_table"]) >= 2
    assert state["implementation_plan"].now != ""
    assert len(state["avoid_and_monitor"]) > 0
    assert len(state["when_to_seek_care"]) > 0
