from typing import Literal

from ..cache import TTLCache

Role = Literal["user", "assistant"]


class ChatHistory:
    """
    Lưu history theo session_id trong TTLCache. Mỗi lần append sẽ set lại key
    nên TTL được làm mới; session không hoạt động quá TTL sẽ tự bị xoá.
    Chỉ giữ max_messages message gần nhất để prompt không phình to.
    """

    def __init__(self, cache: TTLCache, max_messages: int = 20):
        self.cache = cache
        self.max_messages = max_messages

    def _key(self, session_id: str) -> str:
        return f"chat:history:{session_id}"

    def get(self, session_id: str) -> list[dict]:
        messages = self.cache.get(self._key(session_id))

        # Trả về bản copy để code bên ngoài không sửa trực tiếp dữ liệu trong cache
        return list(messages) if messages else []

    def append(self, session_id: str, role: Role, content: str) -> None:
        messages = self.get(session_id)
        messages.append({"role": role, "content": content})

        self.cache.set(self._key(session_id), messages[-self.max_messages:])

    def clear(self, session_id: str) -> None:
        self.cache.delete(self._key(session_id))
