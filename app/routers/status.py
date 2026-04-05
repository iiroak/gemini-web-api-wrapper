from __future__ import annotations

from fastapi import APIRouter, Depends

from gemini_webapi import GeminiClient
from gemini_webapi.utils import rotate_1psidts

from ..auth import verify_api_key
from ..dependencies import get_client
from ..database import save_cookies_to_db

router = APIRouter(tags=["status"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/status", dependencies=[Depends(verify_api_key)])
async def account_status(client: GeminiClient = Depends(get_client)):
    info = await client.inspect_account_status()
    return info


@router.get("/cookies", dependencies=[Depends(verify_api_key)])
async def get_cookies(client: GeminiClient = Depends(get_client)):
    cookies = client.cookies
    result = {}
    for cookie in cookies.jar:
        name = cookie.name
        value = cookie.value or ""
        masked = value[:4] + "***" + value[-4:] if len(value) > 8 else "***"
        result[name] = masked
    return {"cookies": result}


@router.post("/cookies/rotate", dependencies=[Depends(verify_api_key)])
async def force_rotate(client: GeminiClient = Depends(get_client)):
    new_val = await rotate_1psidts(client.client, verbose=True)

    cookie_dict = {}
    for cookie in client.cookies.jar:
        if cookie.name and cookie.value:
            cookie_dict[cookie.name] = cookie.value
    await save_cookies_to_db(cookie_dict)

    return {"rotated": new_val is not None, "message": "Cookies persisted to DB"}
