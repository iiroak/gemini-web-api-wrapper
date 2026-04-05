from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from gemini_webapi import GeminiClient

from ..auth import verify_api_key
from ..dependencies import get_client
from ..serializers import (
    DeepResearchPlanResponse,
    DeepResearchStatusResponse,
    DeepResearchResultResponse,
    to_research_plan_response,
    to_research_status_response,
    to_research_result_response,
)

router = APIRouter(tags=["research"], dependencies=[Depends(verify_api_key)])


class ResearchPromptRequest(BaseModel):
    prompt: str
    model: str | None = None


class StartResearchRequest(BaseModel):
    confirm_prompt: str | None = None


@router.post("/research/plan", response_model=DeepResearchPlanResponse)
async def create_plan(
    body: ResearchPromptRequest, client: GeminiClient = Depends(get_client)
):
    kwargs = {}
    if body.model:
        kwargs["model"] = body.model
    plan = await client.create_deep_research_plan(body.prompt, **kwargs)
    return to_research_plan_response(plan)


@router.post("/research/plan/{research_id}/start")
async def start_research(
    research_id: str,
    body: StartResearchRequest | None = None,
    client: GeminiClient = Depends(get_client),
):
    from gemini_webapi.types.research import DeepResearchPlan

    # Reconstruct minimal plan object with the research_id
    plan = DeepResearchPlan(research_id=research_id)
    kwargs = {}
    if body and body.confirm_prompt:
        kwargs["confirm_prompt"] = body.confirm_prompt
    output = await client.start_deep_research(plan, **kwargs)
    from ..serializers import to_model_output_response
    return to_model_output_response(output)


@router.get("/research/{cid}/status", response_model=DeepResearchStatusResponse)
async def poll_status(cid: str, client: GeminiClient = Depends(get_client)):
    from fastapi import HTTPException

    status = await client.get_deep_research_status(cid)
    if status is None:
        raise HTTPException(status_code=404, detail="Research not found or no status available")
    return to_research_status_response(status)


@router.post("/research", response_model=DeepResearchResultResponse)
async def full_research(
    body: ResearchPromptRequest, client: GeminiClient = Depends(get_client)
):
    result = await client.deep_research(body.prompt)
    return to_research_result_response(result)


@router.post("/research/stream")
async def full_research_stream(
    body: ResearchPromptRequest, client: GeminiClient = Depends(get_client)
):
    async def event_generator():
        plan = await client.create_deep_research_plan(body.prompt)
        plan_data = to_research_plan_response(plan)
        yield f"event: plan\ndata: {plan_data.model_dump_json()}\n\n"

        start_output = await client.start_deep_research(plan)

        statuses_collected = []

        def on_status(s):
            statuses_collected.append(s)

        result = await client.wait_for_deep_research(
            plan, on_status=on_status
        )
        result.start_output = start_output

        for s in statuses_collected:
            s_data = to_research_status_response(s)
            yield f"event: status\ndata: {s_data.model_dump_json()}\n\n"

        result_data = to_research_result_response(result)
        yield f"event: done\ndata: {result_data.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(), media_type="text/event-stream"
    )
