"""Tests for the agents endpoints."""

from fastapi.testclient import TestClient


def test_get_agents_success(client: TestClient):
    """Test GET /agents returns 200 and list of agents."""
    response = client.get("/agents")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    # Check first agent has required fields
    first_agent = data[0]
    assert "key" in first_agent
    assert "name" in first_agent
    assert "description_for_user" in first_agent
    assert "tools" in first_agent
