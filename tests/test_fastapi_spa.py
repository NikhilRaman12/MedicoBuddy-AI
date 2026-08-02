"""Test FastAPI static React SPA serving."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from medicobuddy.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_serves_react_spa(client):
    """GET / should serve index.html from React build."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "MedicoBuddy AI" in response.text
    assert 'id="root"' in response.text


def test_api_routes_remain_intact(client):
    """GET /health/live should remain reachable."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_client_side_subpath_fallback(client):
    """GET /any-client-route should return index.html for client-side routing."""
    response = client.get("/client-route-test")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "MedicoBuddy AI" in response.text


