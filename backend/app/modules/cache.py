import time
from typing import Any, Optional


class TTLCache:
    """
    In-memory cache với TTL, dùng chung cho các module (product_search trước,
    module khác dùng lại sau nếu cần). Không thread-safe theo kiểu multi-process
    (chỉ đúng cho 1 instance backend); nếu scale ra nhiều instance, thay bằng
    Redis (infrastructure/cache/redis.py) mà vẫn giữ nguyên interface get/set.
    """

    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)

        if entry is None:
            return None

        expires_at, value = entry

        if time.time() > expires_at:
            del self._store[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = time.time() + (ttl if ttl is not None else self._default_ttl)
        self._store[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
