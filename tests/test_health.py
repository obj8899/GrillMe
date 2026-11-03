"""Automated sanity and health check tests."""

from fastapi.testclient import TestClient


def test_health_endpoint_api_prefix(client: TestClient) -> None:
    """Verify that GET /api/health returns HTTP 200 with healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "grillme-backend"
    assert "version" in data
    assert "environment" in data


def test_health_endpoint_root_level(client: TestClient) -> None:
    """Verify that GET /health returns HTTP 200 with healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint(client: TestClient) -> None:
    """Verify that GET / returns HTTP 200 with service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "name" in data
