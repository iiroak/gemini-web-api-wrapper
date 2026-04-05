import pytest
from unittest.mock import AsyncMock

from gemini_webapi.exceptions import (
    AuthError,
    UsageLimitExceeded,
    ModelInvalid,
    TemporarilyBlocked,
    TimeoutError,
    GeminiError,
)


@pytest.mark.asyncio
async def test_auth_error_returns_502(client, auth_headers, mock_client):
    mock_client.list_models.side_effect = AuthError("Bad cookies")
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 502
    assert resp.json()["error"] == "auth_error"


@pytest.mark.asyncio
async def test_usage_limit_returns_429(client, auth_headers, mock_client):
    mock_client.list_models.side_effect = UsageLimitExceeded("Rate limited")
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 429
    assert resp.json()["error"] == "usage_limit_exceeded"


@pytest.mark.asyncio
async def test_model_invalid_returns_400(client, auth_headers, mock_client):
    mock_client.list_models.side_effect = ModelInvalid("Invalid model")
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["error"] == "model_invalid"


@pytest.mark.asyncio
async def test_temporarily_blocked_returns_503(client, auth_headers, mock_client):
    mock_client.list_models.side_effect = TemporarilyBlocked("IP blocked")
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 503
    assert resp.json()["error"] == "temporarily_blocked"


@pytest.mark.asyncio
async def test_timeout_returns_504(client, auth_headers, mock_client):
    mock_client.list_models.side_effect = TimeoutError("Timed out")
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 504
    assert resp.json()["error"] == "timeout"


@pytest.mark.asyncio
async def test_generic_gemini_error_returns_502(client, auth_headers, mock_client):
    mock_client.list_models.side_effect = GeminiError("Something went wrong")
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 502
    assert resp.json()["error"] == "gemini_error"
