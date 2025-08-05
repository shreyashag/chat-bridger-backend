import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from src.api.api import app


@pytest.fixture(scope="session")
def test_config():
    """Override config for testing with isolated test environment."""
    test_env = {
        # Use test database (SQLite in-memory or test Supabase)
        "SUPABASE_URL": "http://localhost:54321",  # Local Supabase or test instance
        "SUPABASE_KEY": "test_supabase_key_placeholder",
        # Test API keys
        "OPENROUTER_KEY": "test_openrouter_key",
        "OPENAI_API_KEY": "test_openai_key",
        # Test configuration
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",  # Longer expiry for tests
        # Disable external service calls in tests
        "API_TITLE": "Test Actors API",
    }

    with patch.dict(os.environ, test_env, clear=False):
        # Clear the config cache to use new environment
        from src.config import get_config

        get_config.cache_clear()
        yield


@pytest.fixture
def client(test_config):
    """Create a test client with test configuration."""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Create a test user and return auth token."""
    # Register test user
    register_data = {
        "email": "test@example.com",
        "password": "password123",
        "username": "testuser",
    }
    register_response = client.post("/auth/register", json=register_data)

    # Login and get token
    login_data = {"email": "test@example.com", "password": "password123"}
    login_response = client.post("/auth/login", json=login_data)

    if login_response.status_code == 200:
        return login_response.json()["access_token"]

    # If user already exists, just try to login
    if register_response.status_code == 400:
        if login_response.status_code == 200:
            return login_response.json()["access_token"]

    raise Exception(f"Failed to get auth token: {login_response.text}")


@pytest.fixture
def authenticated_client(client, auth_token):
    """Create a test client with authentication headers."""
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client
