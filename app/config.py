from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _config_dir() -> Path:
    env = os.environ.get("GEMINI_WEB_HOME")
    if env:
        return Path(env)
    # User-level config
    user_dir = Path.home() / ".gemini-web"
    if (user_dir / "config.json").exists():
        return user_dir
    # System-wide fallback (created by install.sh)
    system_dir = Path("/opt/gemini-web/data")
    if (system_dir / "config.json").exists():
        return system_dir
    return user_dir


def _load_user_config() -> dict:
    """Load ~/.gemini-web/config.json if it exists."""
    f = _config_dir() / "config.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _user_db_path() -> str:
    """Default DB path inside the user config dir."""
    return str(_config_dir() / "gemini.db")


# Pre-load user config so it can be used as defaults
_user_cfg = _load_user_config()


class Settings(BaseSettings):
    # No .env — all config comes from CLI (~/.gemini-web/config.json) or env vars
    model_config = {"env_file_encoding": "utf-8"}

    API_KEY: str = _user_cfg.get("API_KEY", "changeme")
    GEMINI_SECURE_1PSID: str = _user_cfg.get("GEMINI_SECURE_1PSID", "")
    GEMINI_SECURE_1PSIDTS: str = _user_cfg.get("GEMINI_SECURE_1PSIDTS", "")
    GEMINI_PROXY: str | None = _user_cfg.get("GEMINI_PROXY") or None
    GEMINI_MODEL: str = _user_cfg.get("GEMINI_MODEL", "UNSPECIFIED")
    GEMINI_TIMEOUT: float = float(_user_cfg.get("GEMINI_TIMEOUT", 450))
    GEMINI_WATCHDOG_TIMEOUT: float = float(_user_cfg.get("GEMINI_WATCHDOG_TIMEOUT", 90))
    GEMINI_AUTO_REFRESH: bool = _user_cfg.get("GEMINI_AUTO_REFRESH", True)
    DATABASE_PATH: str = _user_cfg.get("DATABASE_PATH", _user_db_path())
    LOCAL_NO_AUTH: bool = _user_cfg.get("LOCAL_NO_AUTH", False)
    HOST: str = _user_cfg.get("HOST", "0.0.0.0")
    PORT: int = int(_user_cfg.get("PORT", 8000))


settings = Settings()
