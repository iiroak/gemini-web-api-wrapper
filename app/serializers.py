from __future__ import annotations

from pydantic import BaseModel

from gemini_webapi.types import (
    Candidate,
    ModelOutput,
    ChatInfo,
    ChatTurn,
    ChatHistory,
    Gem,
    AvailableModel,
    WebImage,
    GeneratedImage,
    GeneratedVideo,
    GeneratedMedia,
)
from gemini_webapi.types.research import DeepResearchPlan, DeepResearchStatus
from gemini_webapi.types.researchresult import DeepResearchResult


# ── Images / Videos ──────────────────────────────────────────────

class ImageResponse(BaseModel):
    url: str
    title: str = ""
    alt: str = ""


class VideoResponse(BaseModel):
    url: str
    title: str = ""
    thumbnail_url: str | None = None


class MediaResponse(BaseModel):
    url: str
    title: str = ""
    mp3_url: str | None = None
    thumbnail_url: str | None = None


# ── Candidate / ModelOutput ──────────────────────────────────────

class CandidateResponse(BaseModel):
    rcid: str
    text: str
    text_delta: str | None = None
    thoughts: str | None = None
    thoughts_delta: str | None = None
    web_images: list[ImageResponse] = []
    generated_images: list[ImageResponse] = []
    generated_videos: list[VideoResponse] = []
    generated_media: list[MediaResponse] = []


class ModelOutputResponse(BaseModel):
    metadata: list[str | None] = []
    candidates: list[CandidateResponse] = []
    chosen: int = 0
    text: str = ""
    text_delta: str = ""
    thoughts: str | None = None
    thoughts_delta: str = ""


# ── Chat ─────────────────────────────────────────────────────────

class ChatInfoResponse(BaseModel):
    cid: str
    title: str
    is_pinned: bool = False
    timestamp: float


class ChatTurnResponse(BaseModel):
    role: str
    text: str


class ChatHistoryResponse(BaseModel):
    cid: str
    turns: list[ChatTurnResponse] = []


# ── Gems ─────────────────────────────────────────────────────────

class GemResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    prompt: str | None = None
    predefined: bool


# ── Models ───────────────────────────────────────────────────────

class AvailableModelResponse(BaseModel):
    model_id: str
    model_name: str
    display_name: str
    description: str
    capacity: int
    is_available: bool = True


# ── Deep Research ────────────────────────────────────────────────

class DeepResearchPlanResponse(BaseModel):
    research_id: str | None = None
    title: str | None = None
    query: str | None = None
    steps: list[str] = []
    eta_text: str | None = None
    cid: str | None = None


class DeepResearchStatusResponse(BaseModel):
    research_id: str
    state: str = "running"
    title: str | None = None
    done: bool = False
    notes: list[str] = []


class DeepResearchResultResponse(BaseModel):
    plan: DeepResearchPlanResponse
    done: bool = False
    text: str = ""
    statuses: list[DeepResearchStatusResponse] = []


# ── Converter functions ──────────────────────────────────────────

def _to_image_response(img) -> ImageResponse:
    return ImageResponse(
        url=img.url or "",
        title=getattr(img, "title", "") or "",
        alt=getattr(img, "alt", "") or "",
    )


def _to_video_response(vid) -> VideoResponse:
    return VideoResponse(
        url=vid.url or "",
        title=getattr(vid, "title", "") or "",
        thumbnail_url=getattr(vid, "thumbnail", None),
    )


def _to_media_response(m) -> MediaResponse:
    return MediaResponse(
        url=m.url or "",
        title=getattr(m, "title", "") or "",
        mp3_url=getattr(m, "mp3_url", None),
        thumbnail_url=getattr(m, "thumbnail", None),
    )


def _to_candidate_response(c: Candidate) -> CandidateResponse:
    return CandidateResponse(
        rcid=c.rcid,
        text=c.text,
        text_delta=c.text_delta,
        thoughts=c.thoughts,
        thoughts_delta=c.thoughts_delta,
        web_images=[_to_image_response(i) for i in c.web_images],
        generated_images=[_to_image_response(i) for i in c.generated_images],
        generated_videos=[_to_video_response(v) for v in c.generated_videos],
        generated_media=[_to_media_response(m) for m in c.generated_media],
    )


def to_model_output_response(output: ModelOutput) -> ModelOutputResponse:
    return ModelOutputResponse(
        metadata=list(output.metadata),
        candidates=[_to_candidate_response(c) for c in output.candidates],
        chosen=output.chosen,
        text=output.text,
        text_delta=output.text_delta,
        thoughts=output.thoughts,
        thoughts_delta=output.thoughts_delta,
    )


def to_chat_info_response(info: ChatInfo) -> ChatInfoResponse:
    return ChatInfoResponse(
        cid=info.cid,
        title=info.title,
        is_pinned=info.is_pinned,
        timestamp=info.timestamp,
    )


def to_chat_history_response(history: ChatHistory) -> ChatHistoryResponse:
    return ChatHistoryResponse(
        cid=history.cid,
        turns=[ChatTurnResponse(role=t.role, text=t.text) for t in history.turns],
    )


def to_gem_response(gem: Gem) -> GemResponse:
    return GemResponse(
        id=gem.id,
        name=gem.name,
        description=gem.description,
        prompt=gem.prompt,
        predefined=gem.predefined,
    )


def to_available_model_response(m: AvailableModel) -> AvailableModelResponse:
    return AvailableModelResponse(
        model_id=m.model_id,
        model_name=m.model_name,
        display_name=m.display_name,
        description=m.description,
        capacity=m.capacity,
        is_available=m.is_available,
    )


def to_research_plan_response(plan: DeepResearchPlan) -> DeepResearchPlanResponse:
    return DeepResearchPlanResponse(
        research_id=plan.research_id,
        title=plan.title,
        query=plan.query,
        steps=list(plan.steps),
        eta_text=plan.eta_text,
        cid=plan.cid,
    )


def to_research_status_response(s: DeepResearchStatus) -> DeepResearchStatusResponse:
    return DeepResearchStatusResponse(
        research_id=s.research_id,
        state=s.state,
        title=s.title,
        done=s.done,
        notes=list(s.notes),
    )


def to_research_result_response(r: DeepResearchResult) -> DeepResearchResultResponse:
    return DeepResearchResultResponse(
        plan=to_research_plan_response(r.plan),
        done=r.done,
        text=r.text,
        statuses=[to_research_status_response(s) for s in r.statuses],
    )
