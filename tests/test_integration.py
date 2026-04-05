"""
Integration tests — hit the real Gemini API through the FastAPI wrapper.

Run with:  pytest tests/test_integration.py -v -s
Requires a valid .env with real cookies and API_KEY.

Starts the uvicorn server as a subprocess so curl_cffi gets its own event loop.
"""
from __future__ import annotations

import os
import sys
import time
import subprocess
import socket
from pathlib import Path

import pytest
import httpx

# Skip the entire module if env var signals "skip integration"
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION", "").lower() in ("1", "true", "yes"),
    reason="SKIP_INTEGRATION is set",
)

_PORT = 18923  # unlikely to collide


def _wait_for_server(host: str, port: int, timeout: float = 120) -> None:
    """Block until the server accepts TCP connections or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except OSError:
            time.sleep(1)
    raise RuntimeError(f"Server did not start within {timeout}s")


def _load_api_key() -> str:
    """Read API_KEY from ~/.gemini-web/config.json or environment."""
    key = os.getenv("API_KEY")
    if key:
        return key
    cfg_path = os.path.join(str(Path.home()), ".gemini-web", "config.json")
    if os.path.isfile(cfg_path):
        import json
        with open(cfg_path) as f:
            cfg = json.load(f)
            if cfg.get("API_KEY"):
                return cfg["API_KEY"]
    return "changeme"


@pytest.fixture(scope="module")
def base_url():
    return f"http://127.0.0.1:{_PORT}"


@pytest.fixture(scope="module")
def api_key():
    return _load_api_key()


@pytest.fixture(scope="module", autouse=True)
def server_process(tmp_path_factory):
    """Launch the real uvicorn server as a subprocess for the entire module.

    Stdout/stderr go to a temp log file — using subprocess.PIPE fills the
    64 KB OS buffer on Windows and deadlocks the server event loop.
    """
    log_file = tmp_path_factory.mktemp("server") / "uvicorn.log"
    fh = open(log_file, "w")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", str(_PORT),
        ],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        stdout=fh,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_server("127.0.0.1", _PORT)
        yield proc
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        fh.close()
        print(f"\n--- Server log: {log_file} ---")
        print(log_file.read_text(errors="replace")[-2000:])


# ── Health / status ──────────────────────────────────────────────


def test_health(base_url):
    r = httpx.get(f"{base_url}/health", timeout=30)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_account_status(base_url, api_key):
    r = httpx.get(
        f"{base_url}/status",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)


def test_cookies_redacted(base_url, api_key):
    r = httpx.get(
        f"{base_url}/cookies",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    assert r.status_code == 200
    cookies = r.json()["cookies"]
    for val in cookies.values():
        assert "***" in val


# ── Models ───────────────────────────────────────────────────────


def test_list_models(base_url, api_key):
    r = httpx.get(
        f"{base_url}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    assert r.status_code == 200
    models = r.json()
    assert isinstance(models, list)
    assert len(models) > 0
    assert "display_name" in models[0]


# ── Chat (real round-trip) ───────────────────────────────────────


def test_send_message_real(base_url, api_key):
    """Send a simple prompt and verify we get a non-empty text response."""
    r = httpx.post(
        f"{base_url}/chat/send",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"prompt": "Respond with exactly: INTEGRATION_OK"},
        timeout=480,
    )
    assert r.status_code == 200
    data = r.json()
    assert "candidates" in data
    assert len(data["candidates"]) > 0
    assert len(data["candidates"][0]["text"]) > 0


def test_send_message_stream_real(base_url, api_key):
    """Send a streaming request and verify we receive SSE chunks."""
    with httpx.stream(
        "POST",
        f"{base_url}/chat/send/stream",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"prompt": "Say hello in one word"},
        timeout=480,
    ) as resp:
        assert resp.status_code == 200
        chunks = []
        for line in resp.iter_lines():
            if line.startswith("data:"):
                chunks.append(line)
        assert len(chunks) > 0


def test_list_chats_real(base_url, api_key):
    r = httpx.get(
        f"{base_url}/chats",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
