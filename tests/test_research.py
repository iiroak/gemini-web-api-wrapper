import json

import pytest


@pytest.mark.asyncio
async def test_create_plan(client, auth_headers):
    resp = await client.post(
        "/research/plan",
        json={"prompt": "What is AI?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["research_id"] == "res_1"
    assert data["title"] == "Test Research"
    assert len(data["steps"]) == 3


@pytest.mark.asyncio
async def test_poll_status(client, auth_headers):
    resp = await client.get("/research/res_1/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["research_id"] == "res_1"
    assert data["state"] == "running"


@pytest.mark.asyncio
async def test_full_research_blocking(client, auth_headers):
    resp = await client.post(
        "/research",
        json={"prompt": "What is AI?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["text"] == "Final research report"
    assert len(data["statuses"]) >= 1


@pytest.mark.asyncio
async def test_full_research_stream(client, auth_headers):
    resp = await client.post(
        "/research/stream",
        json={"prompt": "What is AI?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.text
    assert "event: plan" in body
    assert "event: done" in body
