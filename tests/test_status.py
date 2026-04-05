import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_account_status(client, auth_headers):
    resp = await client.get("/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "available"


@pytest.mark.asyncio
async def test_cookies_redacted(client, auth_headers):
    resp = await client.get("/cookies", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "cookies" in data
    cookies = data["cookies"]
    # Values should be masked
    for name, val in cookies.items():
        assert "***" in val


@pytest.mark.asyncio
async def test_force_rotate(client, auth_headers):
    with patch("app.routers.status.rotate_1psidts", new_callable=AsyncMock) as mock_rotate:
        mock_rotate.return_value = "new_token_value"
        with patch("app.routers.status.save_cookies_to_db", new_callable=AsyncMock) as mock_save:
            resp = await client.post("/cookies/rotate", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["rotated"] is True
            mock_save.assert_called_once()
