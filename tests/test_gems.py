import pytest


@pytest.mark.asyncio
async def test_list_gems(client, auth_headers):
    resp = await client.get("/gems", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "TestGem"


@pytest.mark.asyncio
async def test_create_gem(client, auth_headers):
    resp = await client.post(
        "/gems",
        json={"name": "New Gem", "prompt": "Be creative", "description": "Creative gem"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "TestGem"  # mock returns the default


@pytest.mark.asyncio
async def test_update_gem(client, auth_headers):
    resp = await client.put(
        "/gems/gem_1",
        json={"name": "Updated Gem", "prompt": "Be extra creative"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_gem(client, auth_headers):
    resp = await client.delete("/gems/gem_1", headers=auth_headers)
    assert resp.status_code == 204
