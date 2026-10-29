from datetime import datetime, timezone
from typing import Literal, Optional, Protocol

from ..cache import TTLCache

Role = Literal["user", "assistant"]


class ChatHistory(Protocol):
    """Interface chung cho nơi lưu history (in-memory hoặc database)."""

    def get(self, session_id: str, limit: Optional[int] = None) -> list[dict]: ...

    def add_messages(self, session_id: str, messages: list[dict]) -> None: ...

    def exists(self, session_id: str) -> bool: ...

    def clear(self, session_id: str) -> bool: ...


class InMemoryChatHistory:
    """
    Lưu history theo session_id trong TTLCache. Mỗi lần ghi sẽ set lại key
    nên TTL được làm mới; session không hoạt động quá TTL sẽ tự bị xoá.
    Dùng khi chưa cấu hình DATABASE_URI và trong unit test.
    """

    def __init__(self, cache: Optional[TTLCache] = None, max_messages: int = 100):
        self.cache = cache or TTLCache(default_ttl=1800)
        self.max_messages = max_messages

    def _key(self, session_id: str) -> str:
        return f"chat:history:{session_id}"

    def get(self, session_id: str, limit: Optional[int] = None) -> list[dict]:
        messages = self.cache.get(self._key(session_id)) or []

        if limit is not None:
            messages = messages[-limit:] if limit > 0 else []

        # Trả về bản copy để code bên ngoài không sửa trực tiếp dữ liệu trong cache
        return [dict(message) for message in messages]

    def add_messages(self, session_id: str, messages: list[dict]) -> None:
        stored = self.get(session_id)
        now = datetime.now(timezone.utc)

        for message in messages:
            stored.append({"role": message["role"], "content": message["content"], "created_at": now})

        self.cache.set(self._key(session_id), stored[-self.max_messages:])

    def exists(self, session_id: str) -> bool:
        return self.cache.get(self._key(session_id)) is not None

    def clear(self, session_id: str) -> bool:
        existed = self.exists(session_id)
        self.cache.delete(self._key(session_id))

        return existed
