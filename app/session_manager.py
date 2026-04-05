from __future__ import annotations

from gemini_webapi import GeminiClient, ChatSession


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, ChatSession] = {}

    def get(self, cid: str) -> ChatSession | None:
        return self._sessions.get(cid)

    def register(self, chat: ChatSession) -> None:
        if chat.cid:
            self._sessions[chat.cid] = chat

    def create(self, client: GeminiClient, **kwargs) -> ChatSession:
        chat = client.start_chat(**kwargs)
        return chat

    def remove(self, cid: str) -> None:
        self._sessions.pop(cid, None)

    def list_active(self) -> list[str]:
        return list(self._sessions.keys())
