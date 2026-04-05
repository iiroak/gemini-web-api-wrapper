import pytest


@pytest.mark.asyncio
async def test_no_auth_returns_401(client):
    resp = await client.get("/models")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_token_returns_401(client):
    resp = await client.get("/models", headers={"Authorization": "Bearer wrong-key"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_valid_token_passes(client, auth_headers):
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_no_auth_required(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
