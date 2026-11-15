"""Redis-backed chat memory (one list per session)."""
import json

import redis

from app.core.config import Settings

ChatMessage = dict[str, str]


class ChatMemory:
    def __init__(self, client: redis.Redis, settings: Settings) -> None:
        self._client = client
        self._max = settings.memory_max_messages
        self._ttl = settings.memory_ttl_seconds

    @staticmethod
    def _key(session_id: str) -> str:
        return f"chat:{session_id}"

    def get_history(self, session_id: str) -> list[ChatMessage]:
        raw = self._client.lrange(self._key(session_id), 0, -1)
        return [json.loads(item) for item in raw]  # type: ignore[union-attr]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        key = self._key(session_id)
        self._client.rpush(key, json.dumps({"role": role, "content": content}))
        self._client.ltrim(key, -self._max, -1)  # keep only the latest N messages
        self._client.expire(key, self._ttl)
