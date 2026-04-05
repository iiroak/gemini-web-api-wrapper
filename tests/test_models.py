import pytest


@pytest.mark.asyncio
async def test_list_models(client, auth_headers):
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["model_name"] == "gemini-3-flash"
    assert data[0]["display_name"] == "Flash"
    assert data[0]["is_available"] is True


@pytest.mark.asyncio
async def test_list_models_empty(client, auth_headers, mock_client):
    mock_client.list_models.return_value = None
    resp = await client.get("/models", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []
