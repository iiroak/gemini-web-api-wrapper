from __future__ import annotations

import aiosqlite
from datetime import datetime, timezone
from pathlib import Path

from .config import settings

_db_path: str = settings.DATABASE_PATH


def set_db_path(path: str) -> None:
    global _db_path
    _db_path = path


async def get_db() -> aiosqlite.Connection:
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(_db_path)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS cookie_current (
                name  TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cookies (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                value      TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chat_sessions (
                cid        TEXT PRIMARY KEY,
                model      TEXT,
                gem_id     TEXT,
                created_at TEXT NOT NULL,
                last_used_at TEXT NOT NULL
            );
            """
        )
        await db.commit()
    finally:
        await db.close()


async def save_cookies_to_db(cookies: dict[str, str]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        for name, value in cookies.items():
            await db.execute(
                "INSERT OR REPLACE INTO cookie_current (name, value, updated_at) VALUES (?, ?, ?)",
                (name, value, now),
            )
            await db.execute(
                "INSERT INTO cookies (name, value, updated_at) VALUES (?, ?, ?)",
                (name, value, now),
            )
        await db.commit()
    finally:
        await db.close()


async def load_cookies_from_db() -> dict[str, str] | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT name, value FROM cookie_current")
        rows = await cursor.fetchall()
        if not rows:
            return None
        return {row["name"]: row["value"] for row in rows}
    finally:
        await db.close()


async def save_chat_session(cid: str, model: str | None = None, gem_id: str | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO chat_sessions (cid, model, gem_id, created_at, last_used_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(cid) DO UPDATE SET last_used_at = ?, model = COALESCE(?, model), gem_id = COALESCE(?, gem_id)""",
            (cid, model, gem_id, now, now, now, model, gem_id),
        )
        await db.commit()
    finally:
        await db.close()
