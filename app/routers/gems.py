from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from gemini_webapi import GeminiClient

from ..auth import verify_api_key
from ..dependencies import get_client
from ..serializers import GemResponse, to_gem_response

router = APIRouter(tags=["gems"], dependencies=[Depends(verify_api_key)])


class CreateGemRequest(BaseModel):
    name: str
    prompt: str
    description: str = ""


class UpdateGemRequest(BaseModel):
    name: str
    prompt: str
    description: str = ""


@router.get("/gems", response_model=list[GemResponse])
async def list_gems(client: GeminiClient = Depends(get_client)):
    jar = await client.fetch_gems()
    return [to_gem_response(g) for g in jar]


@router.post("/gems", response_model=GemResponse, status_code=201)
async def create_gem(body: CreateGemRequest, client: GeminiClient = Depends(get_client)):
    gem = await client.create_gem(
        name=body.name, prompt=body.prompt, description=body.description
    )
    return to_gem_response(gem)


@router.put("/gems/{gem_id}", response_model=GemResponse)
async def update_gem(
    gem_id: str, body: UpdateGemRequest, client: GeminiClient = Depends(get_client)
):
    gem = await client.update_gem(
        gem=gem_id, name=body.name, prompt=body.prompt, description=body.description
    )
    return to_gem_response(gem)


@router.delete("/gems/{gem_id}", status_code=204)
async def delete_gem(gem_id: str, client: GeminiClient = Depends(get_client)):
    await client.delete_gem(gem=gem_id)
