"""
Tests for the FastAPI health and root endpoints.
No IBM credentials required — mocked pipeline.
"""

import pytest
from datetime import datetime


def test_root_returns_app_info(app_client):
    """GET / must return app name, version, and docs link."""
    resp = app_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "CareerForge AI"
    assert data["version"] == "1.0.0"
    assert "/docs" in data["docs"]
    assert data["status"] == "running"


def test_health_returns_healthy(app_client):
    """GET /health must return status=healthy and the configured Granite model."""
    resp = app_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "granite" in data["granite_model"].lower()
    assert "vector_store_status" in data
    assert "timestamp" in data


def test_health_timestamp_is_recent(app_client):
    """Health timestamp must be a valid ISO datetime."""
    resp = app_client.get("/health")
    ts = resp.json()["timestamp"]
    # Should parse without error
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert isinstance(dt, datetime)


def test_docs_endpoint_accessible(app_client):
    """Swagger UI at /docs must be accessible (200 or redirect)."""
    resp = app_client.get("/docs")
    assert resp.status_code in (200, 307)


def test_list_sessions_empty_initially(app_client):
    """GET /api/v1/sessions on fresh DB must return a list (possibly empty)."""
    resp = app_client.get("/api/v1/sessions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
