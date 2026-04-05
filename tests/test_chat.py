import json

import pytest


@pytest.mark.asyncio
async def test_send_message(client, auth_headers):
    resp = await client.post(
        "/chat/send",
        json={"prompt": "Hello"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert data["text"] == "Hello from Gemini"
    assert "metadata" in data
    assert len(data["candidates"]) >= 1


@pytest.mark.asyncio
async def test_send_message_with_cid(client, auth_headers, mock_client):
    # First send to populate session
    resp1 = await client.post(
        "/chat/send",
        json={"prompt": "Hello"},
        headers=auth_headers,
    )
    cid = resp1.json()["metadata"][0]

    # Continue with cid
    resp2 = await client.post(
        "/chat/send",
        json={"prompt": "Follow up", "cid": cid},
        headers=auth_headers,
    )
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_send_message_stream(client, auth_headers):
    resp = await client.post(
        "/chat/send/stream",
        json={"prompt": "Hello streaming"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    body = resp.text
    assert "event: chunk" in body
    assert "event: done" in body

    # Parse the done event
    for line in body.split("\n"):
        if line.startswith("data: ") and "text" in line:
            data = json.loads(line[6:])
            if "text" in data and data.get("text"):
                assert data["text"] == "Hello from Gemini"
                break


@pytest.mark.asyncio
async def test_list_chats(client, auth_headers):
    resp = await client.get("/chats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "cid" in data[0]
    assert "title" in data[0]


@pytest.mark.asyncio
async def test_read_chat_history(client, auth_headers):
    resp = await client.get("/chats/cid_123", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["cid"] == "cid_123"
    assert len(data["turns"]) == 2
    assert data["turns"][0]["role"] == "user"


@pytest.mark.asyncio
async def test_delete_chat(client, auth_headers):
    resp = await client.delete("/chats/cid_123", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_send_with_model_override(client, auth_headers, mock_client):
    resp = await client.post(
        "/chat/send",
        json={"prompt": "Hello", "model": "gemini-3-flash"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
