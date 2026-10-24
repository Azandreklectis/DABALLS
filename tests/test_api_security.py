"""Tests for optional controller bearer-token authentication."""

from fastapi.testclient import TestClient

from daballs.controller.main import app


def test_api_routes_remain_available_without_configured_token(monkeypatch):
    monkeypatch.delenv("DABALLS_API_TOKEN", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/v1/jobs")
    assert response.status_code == 200


def test_health_endpoint_does_not_require_api_token(monkeypatch):
    monkeypatch.setenv("DABALLS_API_TOKEN", "test-secret-token")
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200


def test_api_rejects_missing_bearer_token(monkeypatch):
    monkeypatch.setenv("DABALLS_API_TOKEN", "test-secret-token")
    with TestClient(app) as client:
        response = client.get("/api/v1/jobs")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_api_rejects_invalid_bearer_token(monkeypatch):
    monkeypatch.setenv("DABALLS_API_TOKEN", "test-secret-token")
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/jobs",
            headers={"Authorization": "Bearer incorrect-token"},
        )
    assert response.status_code == 401


def test_api_accepts_valid_bearer_token(monkeypatch):
    monkeypatch.setenv("DABALLS_API_TOKEN", "test-secret-token")
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/jobs",
            headers={"Authorization": "Bearer test-secret-token"},
        )
    assert response.status_code == 200
