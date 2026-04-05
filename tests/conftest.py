from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
import httpx
from fastapi import Depends
from fastapi.security import HTTPBearer

from gemini_webapi.types import (
    Candidate,
    ModelOutput,
    ChatInfo,
    ChatTurn,
    ChatHistory,
    Gem,
    GemJar,
    AvailableModel,
    WebImage,
    GeneratedImage,
)
from gemini_webapi.types.research import DeepResearchPlan, DeepResearchStatus
from gemini_webapi.types.researchresult import DeepResearchResult


# ── Fake data factories ──────────────────────────────────────────

def make_candidate(**overrides) -> Candidate:
    defaults = dict(
        rcid="rc_1",
        text="Hello from Gemini",
        text_delta="Hello from Gemini",
        thoughts=None,
        thoughts_delta=None,
        web_images=[],
        generated_images=[],
        generated_videos=[],
        generated_media=[],
        deep_research_plan=None,
    )
    defaults.update(overrides)
    return Candidate(**defaults)


def make_model_output(**overrides) -> ModelOutput:
    defaults = dict(
        metadata=["cid_123", "rid_456", "rc_1"],
        candidates=[make_candidate()],
        chosen=0,
    )
    defaults.update(overrides)
    return ModelOutput(**defaults)


def make_chat_info(**overrides) -> ChatInfo:
    defaults = dict(cid="cid_123", title="Test chat", is_pinned=False, timestamp=1700000000.0)
    defaults.update(overrides)
    return ChatInfo(**defaults)


def make_chat_history(**overrides) -> ChatHistory:
    defaults = dict(
        cid="cid_123",
        turns=[
            ChatTurn(role="user", text="Hi"),
            ChatTurn(role="model", text="Hello!", model_output=make_model_output()),
        ],
    )
    defaults.update(overrides)
    return ChatHistory(**defaults)


def make_gem(**overrides) -> Gem:
    defaults = dict(id="gem_1", name="TestGem", description="A test gem", prompt="Be helpful", predefined=False)
    defaults.update(overrides)
    return Gem(**defaults)


def make_available_model(**overrides) -> AvailableModel:
    defaults = dict(
        model_id="abc123",
        model_name="gemini-3-flash",
        display_name="Flash",
        description="Fast model",
        capacity=1,
        capacity_field=12,
        is_available=True,
    )
    defaults.update(overrides)
    return AvailableModel(**defaults)


def make_deep_research_plan(**overrides) -> DeepResearchPlan:
    defaults = dict(
        research_id="res_1",
        title="Test Research",
        query="What is AI?",
        steps=["Search", "Analyze", "Summarize"],
        eta_text="~5 minutes",
        cid="cid_res",
    )
    defaults.update(overrides)
    return DeepResearchPlan(**defaults)


def make_deep_research_status(**overrides) -> DeepResearchStatus:
    defaults = dict(
        research_id="res_1",
        state="running",
        title="Test Research",
        done=False,
        notes=["Searching..."],
    )
    defaults.update(overrides)
    return DeepResearchStatus(**defaults)


def make_deep_research_result(**overrides) -> DeepResearchResult:
    defaults = dict(
        plan=make_deep_research_plan(),
        start_output=make_model_output(),
        final_output=make_model_output(
            candidates=[make_candidate(text="Final research report")]
        ),
        statuses=[make_deep_research_status()],
        done=True,
    )
    defaults.update(overrides)
    return DeepResearchResult(**defaults)


# ── Mock ChatSession ─────────────────────────────────────────────

class MockChatSession:
    def __init__(self):
        self.cid = "cid_123"
        self.rid = "rid_456"
        self.rcid = "rc_1"
        self.metadata = ["cid_123", "rid_456", "rc_1"]
        self.last_output = None
        self.model = None
        self.gem = None

    async def send_message(self, prompt, **kwargs):
        return make_model_output()

    async def send_message_stream(self, prompt, **kwargs):
        output = make_model_output()
        yield output


# ── Mock GeminiClient ────────────────────────────────────────────

def create_mock_client():
    client = MagicMock()

    # Core generation
    client.generate_content = AsyncMock(return_value=make_model_output())

    async def _mock_stream(*args, **kwargs):
        yield make_model_output()

    client.generate_content_stream = _mock_stream

    # Chat management
    client.list_chats = MagicMock(return_value=[make_chat_info()])
    client.read_chat = AsyncMock(return_value=make_chat_history())
    client.delete_chat = AsyncMock(return_value=None)
    client.start_chat = MagicMock(return_value=MockChatSession())

    # Models
    client.list_models = MagicMock(return_value=[make_available_model()])

    # Gems
    client.fetch_gems = AsyncMock(return_value=GemJar({make_gem().id: make_gem()}))
    client.create_gem = AsyncMock(return_value=make_gem())
    client.update_gem = AsyncMock(return_value=make_gem(name="Updated"))
    client.delete_gem = AsyncMock(return_value=None)

    # Deep Research
    client.create_deep_research_plan = AsyncMock(return_value=make_deep_research_plan())
    client.start_deep_research = AsyncMock(return_value=make_model_output())
    client.get_deep_research_status = AsyncMock(return_value=make_deep_research_status())
    client.wait_for_deep_research = AsyncMock(return_value=make_deep_research_result())
    client.deep_research = AsyncMock(return_value=make_deep_research_result())

    # Account/status
    client.inspect_account_status = AsyncMock(return_value={"status": "available"})

    # Cookies — use a mock jar
    mock_cookie = MagicMock()
    mock_cookie.name = "__Secure-1PSID"
    mock_cookie.value = "abcdef1234567890"
    mock_cookies = MagicMock()
    mock_cookies.jar = [mock_cookie]
    type(client).cookies = PropertyMock(return_value=mock_cookies)

    # Push ID
    client.push_id = "push_123"

    # HTTP client (for file operations)
    mock_response = MagicMock()
    mock_response.content = b"fake-image-data"
    mock_response.headers = {"content-type": "image/png"}
    client.client = MagicMock()
    client.client.get = AsyncMock(return_value=mock_response)

    return client


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def mock_client():
    return create_mock_client()


@pytest.fixture
async def app_with_mock(mock_client, tmp_path):
    from app.main import app, session_manager
    from app.dependencies import get_client
    from app.auth import verify_api_key
    from app.database import set_db_path, init_db

    # Use a temp DB for tests
    db_path = str(tmp_path / "test_api.db")
    set_db_path(db_path)
    await init_db()

    app.dependency_overrides[get_client] = lambda: mock_client

    # Override auth to accept "test-api-key"
    async def _mock_verify(
        credentials=Depends(HTTPBearer(auto_error=False)),
    ):
        if credentials is None or credentials.credentials != "test-api-key":
            from fastapi import HTTPException as Exc
            raise Exc(status_code=401, detail="Invalid or missing API key")
        return credentials.credentials

    app.dependency_overrides[verify_api_key] = _mock_verify

    # Reset session manager
    session_manager._sessions.clear()

    yield app

    app.dependency_overrides.clear()
    set_db_path("data/gemini.db")


@pytest.fixture
async def client(app_with_mock):
    transport = httpx.ASGITransport(app=app_with_mock)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-api-key"}
