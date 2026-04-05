from __future__ import annotations

from fastapi import Request

from gemini_webapi import GeminiClient


def get_client(request: Request) -> GeminiClient:
    return request.app.state.client
