import os
import tempfile
import sqlite3
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Use a separate test database to avoid affecting actual database data
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_db_path = temp_db.name
temp_db.close()
os.environ["DB_PATH"] = temp_db_path

from backend.main import app, init_db
from backend.services.oauth_service import (
    generate_oauth_state,
    validate_oauth_state,
    sync_oauth_user,
    is_google_configured,
    is_github_configured,
)

client = TestClient(app, follow_redirects=False)

@pytest.fixture(autouse=True, scope="module")
def setup_test_database():
    init_db()
    yield
    try:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
    except Exception:
        pass


def test_unconfigured_oauth_url_returns_400():
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": ""}):
        res = client.get("/auth/google/url")
        assert res.status_code == 400
        assert "Google OAuth is not configured" in res.json()["detail"]

    with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "", "GITHUB_CLIENT_SECRET": ""}):
        res = client.get("/auth/github/url")
        assert res.status_code == 400
        assert "GitHub OAuth is not configured" in res.json()["detail"]


def test_unconfigured_direct_oauth_redirects_to_login():
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": ""}):
        res = client.get("/auth/google")
        assert res.status_code in (302, 307)
        assert "/login?error=" in res.headers["location"]

    with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "", "GITHUB_CLIENT_SECRET": ""}):
        res = client.get("/auth/github")
        assert res.status_code in (302, 307)
        assert "/login?error=" in res.headers["location"]


def test_configured_oauth_url_generates_valid_provider_url():
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "mock-google-id", "GOOGLE_CLIENT_SECRET": "mock-google-secret"}):
        res = client.get("/auth/google/url?redirect_to=/app/analytics")
        assert res.status_code == 200
        url = res.json()["url"]
        assert "accounts.google.com" in url
        assert "client_id=mock-google-id" in url
        assert "state=" in url

    with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "mock-github-id", "GITHUB_CLIENT_SECRET": "mock-github-secret"}):
        res = client.get("/auth/github/url")
        assert res.status_code == 200
        url = res.json()["url"]
        assert "github.com/login/oauth/authorize" in url
        assert "client_id=mock-github-id" in url
        assert "state=" in url


def test_oauth_state_generation_and_validation():
    state = generate_oauth_state("google", "/app/schema")
    payload = validate_oauth_state(state, expected_provider="google")
    assert payload is not None
    assert payload["provider"] == "google"
    assert payload["redirect_to"] == "/app/schema"

    # Mismatched provider should fail
    assert validate_oauth_state(state, expected_provider="github") is None

    # Tampered state should fail
    assert validate_oauth_state(state + "corrupted", expected_provider="google") is None


def test_sync_oauth_user_creation_and_linking():
    # 1. First login: creates new user
    user_info = {
        "provider": "google",
        "provider_id": "google_12345",
        "email": "test_oauth_user@example.com",
        "name": "Test User",
        "avatar_url": "https://example.com/avatar.jpg"
    }

    result = sync_oauth_user(user_info)
    assert result["access_token"] is not None
    assert result["refresh_token"] is not None
    user = result["user"]
    assert user["email"] == "test_oauth_user@example.com"
    assert user["role"] == "Admin"
    assert user["oauth_provider"] == "google"
    assert user["oauth_provider_id"] == "google_12345"
    user_id = user["id"]

    # 2. Subsequent login with same provider_id returns same user (no duplicates)
    second_result = sync_oauth_user(user_info)
    assert second_result["user"]["id"] == user_id

    # 3. Login with another provider with same email links to existing account
    github_user_info = {
        "provider": "github",
        "provider_id": "github_99999",
        "email": "test_oauth_user@example.com",
        "name": "Test User GitHub",
        "avatar_url": "https://example.com/gh-avatar.jpg"
    }
    linked_result = sync_oauth_user(github_user_info)
    assert linked_result["user"]["id"] == user_id


@pytest.mark.asyncio
async def test_oauth_callback_flow():
    state = generate_oauth_state("google", "/app")
    mock_google_profile = {
        "provider": "google",
        "provider_id": "g_sub_111",
        "email": "callback_test@example.com",
        "name": "Callback User",
        "avatar_url": "https://example.com/pic.png",
    }

    with patch("backend.routers.auth.exchange_google_code_for_user", new=AsyncMock(return_value=mock_google_profile)):
        res = client.get(f"/auth/google/callback?code=mock_code&state={state}")
        assert res.status_code in (302, 307)
        location = res.headers["location"]
        assert "/auth/callback" in location
        assert "access_token=" in location
        assert "refresh_token=" in location
        assert "redirect=/app" in location
