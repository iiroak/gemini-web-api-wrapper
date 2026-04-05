import pytest
from unittest.mock import patch

from app.database import init_db, save_cookies_to_db, load_cookies_from_db, set_db_path


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    await init_db()
    yield
    set_db_path("data/gemini.db")


@pytest.mark.asyncio
async def test_init_db_creates_tables():
    import aiosqlite
    from app.database import _db_path

    async with aiosqlite.connect(_db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]
        assert "cookie_current" in tables
        assert "cookies" in tables
        assert "chat_sessions" in tables


@pytest.mark.asyncio
async def test_save_and_load_cookies():
    cookies = {"__Secure-1PSID": "sid_value", "__Secure-1PSIDTS": "sidts_value"}
    await save_cookies_to_db(cookies)

    loaded = await load_cookies_from_db()
    assert loaded is not None
    assert loaded["__Secure-1PSID"] == "sid_value"
    assert loaded["__Secure-1PSIDTS"] == "sidts_value"


@pytest.mark.asyncio
async def test_cookie_history_append_only():
    import aiosqlite
    from app.database import _db_path

    # First save
    await save_cookies_to_db({"__Secure-1PSID": "value1"})

    # Second save (different value)
    await save_cookies_to_db({"__Secure-1PSID": "value2"})

    # Current should have latest
    loaded = await load_cookies_from_db()
    assert loaded["__Secure-1PSID"] == "value2"

    # History should have both
    async with aiosqlite.connect(_db_path) as db:
        cursor = await db.execute(
            "SELECT value FROM cookies WHERE name = '__Secure-1PSID' ORDER BY id"
        )
        rows = await cursor.fetchall()
        assert len(rows) == 2
        assert rows[0][0] == "value1"
        assert rows[1][0] == "value2"


@pytest.mark.asyncio
async def test_load_cookies_empty_db():
    loaded = await load_cookies_from_db()
    assert loaded is None
