import time

from backend.app.modules.cache import TTLCache


def test_cache_miss_when_key_not_set():
    cache = TTLCache(default_ttl=60)

    assert cache.get("missing") is None


def test_cache_hit_returns_stored_value():
    cache = TTLCache(default_ttl=60)
    cache.set("query:kem chong nang", ["product_a", "product_b"])

    assert cache.get("query:kem chong nang") == ["product_a", "product_b"]


def test_cache_expires_after_ttl():
    cache = TTLCache(default_ttl=0.05)
    cache.set("query:short-lived", "value")

    assert cache.get("query:short-lived") == "value"

    time.sleep(0.1)

    assert cache.get("query:short-lived") is None


def test_cache_per_key_ttl_overrides_default():
    cache = TTLCache(default_ttl=60)
    cache.set("query:custom-ttl", "value", ttl=0.05)

    time.sleep(0.1)

    assert cache.get("query:custom-ttl") is None


def test_cache_delete_removes_key():
    cache = TTLCache(default_ttl=60)
    cache.set("query:to-delete", "value")
    cache.delete("query:to-delete")

    assert cache.get("query:to-delete") is None


def test_cache_clear_removes_all_keys():
    cache = TTLCache(default_ttl=60)
    cache.set("query:a", "1")
    cache.set("query:b", "2")

    cache.clear()

    assert cache.get("query:a") is None
    assert cache.get("query:b") is None
