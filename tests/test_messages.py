"""Tests for the messages endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient


# class SQLiteSessionWrapper:
#     """Wrapper for SQLiteSession to match SupabaseSession interface."""
#
#     def __init__(self, session_id: str, config=None, agent_key: str = None):
#         self.session_id = session_id
#         self.agent_key = agent_key
#         self._session = SQLiteSession(session_id)
#
#     def get_agent_key(self):
#         return self.agent_key
#
#     def __getattr__(self, name):
#         return getattr(self._session, name)


def test_send_message_what_comes_after_saturday(authenticated_client: TestClient):
    """Test POST /send_message with 'What comes after Saturday' expects 'Sunday' response."""
    with (
        # patch("src.api.routers.chat.SupabaseSession", SQLiteSessionWrapper),
        patch("src.core.agent_factory.create_mcp_servers", return_value=[]),
    ):
        response = authenticated_client.post(
            "/chat/send_message",
            json={
                "session_id": "test_saturday_session",
                "message": "What comes after Saturday?",
                "agent_key": "triage_agent",
                "stream": True,
            },
        )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    assert "sunday" in data["response"].lower()
