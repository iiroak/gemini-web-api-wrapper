from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from gemini_webapi import GeminiClient
from gemini_webapi.exceptions import (
    APIError,
    AuthError,
    GeminiError,
    ModelInvalid,
    TemporarilyBlocked,
    TimeoutError,
    UsageLimitExceeded,
)

from .config import settings
from .database import init_db, load_cookies_from_db, save_cookies_to_db
from .session_manager import SessionManager

session_manager = SessionManager()

_cookie_monitor_task: asyncio.Task | None = None


def _extract_cookie_dict(client: GeminiClient) -> dict[str, str]:
    result = {}
    for cookie in client.cookies.jar:
        if cookie.name and cookie.value:
            result[cookie.name] = cookie.value
    return result


async def _cookie_monitor(client: GeminiClient) -> None:
    last_snapshot: dict[str, str] = {}
    while True:
        await asyncio.sleep(60)
        try:
            current = _extract_cookie_dict(client)
            if current != last_snapshot:
                await save_cookies_to_db(current)
                last_snapshot = dict(current)
                logger.info("Cookie change detected — persisted to DB")
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning(f"Cookie monitor error: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cookie_monitor_task

    # 1. Init database
    await init_db()

    # 2. Load cookies — prefer DB (may be newer from rotation)
    db_cookies = await load_cookies_from_db()
    if db_cookies:
        secure_1psid = db_cookies.get("__Secure-1PSID", settings.GEMINI_SECURE_1PSID)
        secure_1psidts = db_cookies.get("__Secure-1PSIDTS", settings.GEMINI_SECURE_1PSIDTS)
        logger.info("Loaded cookies from database (may be newer from rotation)")
    else:
        secure_1psid = settings.GEMINI_SECURE_1PSID
        secure_1psidts = settings.GEMINI_SECURE_1PSIDTS

    # 3. Create and initialize client
    client = GeminiClient(
        secure_1psid=secure_1psid,
        secure_1psidts=secure_1psidts or None,
        proxy=settings.GEMINI_PROXY,
    )
    await client.init(
        timeout=settings.GEMINI_TIMEOUT,
        auto_refresh=settings.GEMINI_AUTO_REFRESH,
        watchdog_timeout=settings.GEMINI_WATCHDOG_TIMEOUT,
        verbose=True,
    )
    app.state.client = client

    # 4. Persist initial cookies
    await save_cookies_to_db(_extract_cookie_dict(client))

    # 5. Start cookie monitor
    _cookie_monitor_task = asyncio.create_task(_cookie_monitor(client))

    logger.info("Gemini API wrapper started")
    yield

    # Shutdown
    if _cookie_monitor_task:
        _cookie_monitor_task.cancel()
        try:
            await _cookie_monitor_task
        except asyncio.CancelledError:
            pass

    # Persist final cookies
    await save_cookies_to_db(_extract_cookie_dict(client))
    await client.close()
    logger.info("Gemini API wrapper shut down")


# ── App creation ─────────────────────────────────────────────────

app = FastAPI(
    title="Gemini Web API Wrapper",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Exception handlers ───────────────────────────────────────────


@app.exception_handler(AuthError)
async def handle_auth_error(request: Request, exc: AuthError):
    return JSONResponse(status_code=502, content={"error": "auth_error", "message": str(exc)})


@app.exception_handler(UsageLimitExceeded)
async def handle_usage_limit(request: Request, exc: UsageLimitExceeded):
    return JSONResponse(status_code=429, content={"error": "usage_limit_exceeded", "message": str(exc)})


@app.exception_handler(ModelInvalid)
async def handle_model_invalid(request: Request, exc: ModelInvalid):
    return JSONResponse(status_code=400, content={"error": "model_invalid", "message": str(exc)})


@app.exception_handler(TemporarilyBlocked)
async def handle_temporarily_blocked(request: Request, exc: TemporarilyBlocked):
    return JSONResponse(status_code=503, content={"error": "temporarily_blocked", "message": str(exc)})


@app.exception_handler(TimeoutError)
async def handle_timeout(request: Request, exc: TimeoutError):
    return JSONResponse(status_code=504, content={"error": "timeout", "message": str(exc)})


@app.exception_handler(GeminiError)
async def handle_gemini_error(request: Request, exc: GeminiError):
    return JSONResponse(status_code=502, content={"error": "gemini_error", "message": str(exc)})


@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError):
    return JSONResponse(status_code=500, content={"error": "api_error", "message": str(exc)})


# ── Request logging middleware ───────────────────────────────────


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration_ms:.0f}ms)")
    return response


# ── Include routers ──────────────────────────────────────────────

from .routers import chat, models, gems, research, files, status  # noqa: E402

app.include_router(chat.router)
app.include_router(models.router)
app.include_router(gems.router)
app.include_router(research.router)
app.include_router(files.router)
app.include_router(status.router)
