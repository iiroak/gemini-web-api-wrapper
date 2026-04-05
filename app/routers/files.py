from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from gemini_webapi import GeminiClient
from gemini_webapi.utils import upload_file as gemini_upload_file

from ..auth import verify_api_key
from ..dependencies import get_client

router = APIRouter(tags=["files"], dependencies=[Depends(verify_api_key)])


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    client: GeminiClient = Depends(get_client),
):
    content = await file.read()
    ref = await gemini_upload_file(
        file=content,
        client=client.client,
        push_id=client.push_id,
        filename=file.filename,
    )
    return {"reference": ref, "filename": file.filename}


@router.get("/files/download")
async def download_file(
    url: str,
    client: GeminiClient = Depends(get_client),
):
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    response = await client.client.get(url, allow_redirects=True)
    content_type = response.headers.get("content-type", "application/octet-stream")

    return StreamingResponse(
        iter([response.content]),
        media_type=content_type,
        headers={"Content-Disposition": "attachment"},
    )
