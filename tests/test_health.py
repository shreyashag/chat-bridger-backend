"""Tests for the health endpoint."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test the health endpoint returns correct status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
