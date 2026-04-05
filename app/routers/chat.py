from __future__ import annotations

import json
import time
import traceback
from typing import Optional

from fastapi import APIRouter, Depends, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from gemini_webapi import GeminiClient

from ..auth import verify_api_key
from ..dependencies import get_client
from ..database import save_chat_session
from ..serializers import (
    ModelOutputResponse,
    ChatInfoResponse,
    ChatHistoryResponse,
    to_model_output_response,
    to_chat_info_response,
    to_chat_history_response,
)

router = APIRouter(tags=["chat"], dependencies=[Depends(verify_api_key)])


class SendRequest(BaseModel):
    prompt: str
    cid: str | None = None
    model: str | None = None
    gem_id: str | None = None
    temporary: bool = False


@router.post("/chat/send", response_model=ModelOutputResponse)
async def send_message(
    body: SendRequest,
    client: GeminiClient = Depends(get_client),
):
    from ..main import session_manager

    logger.debug(f"[chat/send] prompt={body.prompt[:80]!r} cid={body.cid} model={body.model}")

    chat = None
    if body.cid:
        chat = session_manager.get(body.cid)
    if chat is None:
        chat = session_manager.create(client)
        logger.debug("[chat/send] created new ChatSession")

    if body.model:
        chat.model = body.model
    if body.gem_id:
        chat.gem = body.gem_id

    t0 = time.time()
    logger.info(f"[chat/send] calling chat.send_message ...")
    try:
        output = await chat.send_message(
            body.prompt, temporary=body.temporary,
        )
    except Exception:
        logger.error(f"[chat/send] send_message failed after {time.time()-t0:.1f}s:\n{traceback.format_exc()}")
        raise
    logger.info(f"[chat/send] got response in {time.time()-t0:.1f}s, cid={chat.cid}")

    if chat.cid:
        session_manager.register(chat)
        await save_chat_session(chat.cid, model=body.model, gem_id=body.gem_id)

    return to_model_output_response(output)


@router.post("/chat/send/stream")
async def send_message_stream(
    body: SendRequest,
    client: GeminiClient = Depends(get_client),
):
    from ..main import session_manager

    chat = None
    if body.cid:
        chat = session_manager.get(body.cid)
    if chat is None:
        chat = session_manager.create(client)

    if body.model:
        chat.model = body.model
    if body.gem_id:
        chat.gem = body.gem_id

    async def event_generator():
        last_output = None
        t0 = time.time()
        logger.info("[chat/send/stream] starting stream ...")
        try:
            async for chunk in chat.send_message_stream(
                body.prompt, temporary=body.temporary,
            ):
                last_output = chunk
                data = json.dumps(
                    {
                        "text_delta": chunk.text_delta,
                        "thoughts_delta": chunk.thoughts_delta,
                        "metadata": list(chunk.metadata),
                    },
                    ensure_ascii=False,
                )
                logger.debug(f"[chat/send/stream] chunk delta={chunk.text_delta!r}")
                yield f"event: chunk\ndata: {data}\n\n"
        except Exception:
            logger.error(f"[chat/send/stream] failed after {time.time()-t0:.1f}s:\n{traceback.format_exc()}")
            raise

        logger.info(f"[chat/send/stream] completed in {time.time()-t0:.1f}s")
        if last_output is not None:
            if chat.cid:
                session_manager.register(chat)
                await save_chat_session(chat.cid, model=body.model, gem_id=body.gem_id)
            resp = to_model_output_response(last_output)
            yield f"event: done\ndata: {resp.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(), media_type="text/event-stream"
    )


@router.post("/chat/send/upload", response_model=ModelOutputResponse)
async def send_message_with_files(
    prompt: str = Form(...),
    cid: str | None = Form(None),
    model: str | None = Form(None),
    gem_id: str | None = Form(None),
    temporary: bool = Form(False),
    files: list[UploadFile] = File(default=[]),
    client: GeminiClient = Depends(get_client),
):
    from ..main import session_manager

    chat = None
    if cid:
        chat = session_manager.get(cid)
    if chat is None:
        chat = session_manager.create(client)

    if model:
        chat.model = model
    if gem_id:
        chat.gem = gem_id

    file_bytes_list = []
    for f in files:
        file_bytes_list.append(await f.read())

    output = await chat.send_message(
        prompt,
        files=file_bytes_list if file_bytes_list else None,
        temporary=temporary,
    )

    if chat.cid:
        session_manager.register(chat)
        await save_chat_session(chat.cid, model=model, gem_id=gem_id)

    return to_model_output_response(output)


@router.get("/chats", response_model=list[ChatInfoResponse])
async def list_chats(client: GeminiClient = Depends(get_client)):
    chats = client.list_chats()
    if not chats:
        return []
    return [to_chat_info_response(c) for c in chats]


@router.get("/chats/{cid}", response_model=ChatHistoryResponse)
async def read_chat(cid: str, limit: int = 30, client: GeminiClient = Depends(get_client)):
    history = await client.read_chat(cid, limit=limit)
    if history is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Chat not found")
    return to_chat_history_response(history)


@router.delete("/chats/{cid}", status_code=204)
async def delete_chat(cid: str, client: GeminiClient = Depends(get_client)):
    from ..main import session_manager

    await client.delete_chat(cid)
    session_manager.remove(cid)
