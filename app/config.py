from __future__ import annotations

import json
from pathlib import Path

from pydantic_settings import BaseSettings


def _load_user_config() -> dict:
    """Load ~/.gemini-web/config.json if it exists."""
    f = Path.home() / ".gemini-web" / "config.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _user_db_path() -> str:
    """Default DB path inside the user config dir."""
    return str(Path.home() / ".gemini-web" / "gemini.db")


# Pre-load user config so it can be used as defaults
_user_cfg = _load_user_config()


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    API_KEY: str = _user_cfg.get("API_KEY", "changeme")
    GEMINI_SECURE_1PSID: str = _user_cfg.get("GEMINI_SECURE_1PSID", "")
    GEMINI_SECURE_1PSIDTS: str = _user_cfg.get("GEMINI_SECURE_1PSIDTS", "")
    GEMINI_PROXY: str | None = _user_cfg.get("GEMINI_PROXY") or None
    GEMINI_MODEL: str = _user_cfg.get("GEMINI_MODEL", "UNSPECIFIED")
    GEMINI_TIMEOUT: float = float(_user_cfg.get("GEMINI_TIMEOUT", 450))
    GEMINI_WATCHDOG_TIMEOUT: float = float(_user_cfg.get("GEMINI_WATCHDOG_TIMEOUT", 90))
    GEMINI_AUTO_REFRESH: bool = _user_cfg.get("GEMINI_AUTO_REFRESH", True)
    DATABASE_PATH: str = _user_cfg.get("DATABASE_PATH", _user_db_path())
    HOST: str = _user_cfg.get("HOST", "0.0.0.0")
    PORT: int = int(_user_cfg.get("PORT", 8000))


settings = Settings()
