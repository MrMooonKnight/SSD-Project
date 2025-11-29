"""Simple tests for health endpoints."""

from __future__ import annotations

from backend.app import create_app


def test_live_endpoint_returns_ok():
    app = create_app()
    client = app.test_client()

    response = client.get("/api/health/live")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "alive"


def test_ready_endpoint_returns_checks():
    app = create_app()
    client = app.test_client()

    response = client.get("/api/health/ready")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["checks"]["firestore"] == "deferred"

