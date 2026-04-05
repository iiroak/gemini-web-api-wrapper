import io

import pytest


@pytest.mark.asyncio
async def test_upload_file(client, auth_headers, mock_client):
    from unittest.mock import AsyncMock, patch

    with patch("app.routers.files.gemini_upload_file", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = "/contrib_service/ttl_1d/ref123"

        resp = await client.post(
            "/files/upload",
            headers=auth_headers,
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reference"] == "/contrib_service/ttl_1d/ref123"
        assert data["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_download_proxy(client, auth_headers):
    resp = await client.get(
        "/files/download",
        params={"url": "https://example.com/image.png"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.content == b"fake-image-data"
