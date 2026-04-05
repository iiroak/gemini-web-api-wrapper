from __future__ import annotations

from fastapi import APIRouter, Depends

from gemini_webapi import GeminiClient

from ..auth import verify_api_key
from ..dependencies import get_client
from ..serializers import AvailableModelResponse, to_available_model_response

router = APIRouter(tags=["models"], dependencies=[Depends(verify_api_key)])


@router.get("/models", response_model=list[AvailableModelResponse])
async def list_models(client: GeminiClient = Depends(get_client)):
    models = client.list_models()
    if not models:
        return []
    return [to_available_model_response(m) for m in models]
