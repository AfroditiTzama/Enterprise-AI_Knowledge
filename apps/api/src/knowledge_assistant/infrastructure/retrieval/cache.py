import time
from dataclasses import dataclass

from knowledge_assistant.domain.chat.entities import KnowledgeChatResult


@dataclass
class _CacheEntry:
    expires_at: float
    value: KnowledgeChatResult


class LocalRAGResponseCache:
    def __init__(self, *, ttl_seconds: int = 300, max_entries: int = 256) -> None:
        self._ttl_seconds = max(0, ttl_seconds)
        self._max_entries = max(1, max_entries)
        self._entries: dict[str, _CacheEntry] = {}

    def get(self, key: str) -> KnowledgeChatResult | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at <= time.monotonic():
            self._entries.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: KnowledgeChatResult) -> None:
        if self._ttl_seconds <= 0:
            return
        if len(self._entries) >= self._max_entries:
            oldest_key = min(
                self._entries,
                key=lambda item: self._entries[item].expires_at,
            )
            self._entries.pop(oldest_key, None)
        self._entries[key] = _CacheEntry(
            expires_at=time.monotonic() + self._ttl_seconds,
            value=value,
        )
