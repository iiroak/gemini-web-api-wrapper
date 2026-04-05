"""
Diagnostic: test GeminiClient directly, no FastAPI involved.
Usage:  python tests/diag_direct.py
"""
import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from gemini_webapi import GeminiClient


async def main():
    print(f"[1] Creating GeminiClient with cookie={settings.GEMINI_SECURE_1PSID[:12]}...")
    client = GeminiClient(
        secure_1psid=settings.GEMINI_SECURE_1PSID,
        secure_1psidts=settings.GEMINI_SECURE_1PSIDTS or None,
        proxy=settings.GEMINI_PROXY,
    )

    print(f"[2] Initializing client (timeout={settings.GEMINI_TIMEOUT})...")
    t0 = time.time()
    await client.init(
        timeout=settings.GEMINI_TIMEOUT,
        auto_refresh=settings.GEMINI_AUTO_REFRESH,
        watchdog_timeout=settings.GEMINI_WATCHDOG_TIMEOUT,
        verbose=True,
    )
    print(f"    init completed in {time.time()-t0:.1f}s")

    print("[3] Sending message: 'Respond with exactly: OK'")
    t0 = time.time()
    response = await client.generate_content("Respond with exactly: OK")
    elapsed = time.time() - t0
    print(f"    response in {elapsed:.1f}s")
    print(f"    text: {response.text!r}")
    print(f"    metadata: {list(response.metadata)}")

    print("[4] Testing stream...")
    t0 = time.time()
    chat = client.start_chat()
    async for chunk in chat.send_message_stream("Say hi in one word"):
        print(f"    chunk delta: {chunk.text_delta!r} ({time.time()-t0:.1f}s)")
    print(f"    stream done in {time.time()-t0:.1f}s")

    await client.close()
    print("[5] DONE - all good!")


if __name__ == "__main__":
    asyncio.run(main())
