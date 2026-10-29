from backend.app.modules.cache import TTLCache
from backend.app.modules.chat.history import InMemoryChatHistory


def turn(user: str, assistant: str) -> list[dict]:
    return [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]


def test_empty_session():
    history = InMemoryChatHistory()

    assert history.get("s1") == []
    assert history.exists("s1") is False


def test_add_and_get_in_order():
    history = InMemoryChatHistory()
    history.add_messages("s1", turn("hi", "hello"))
    history.add_messages("s1", turn("q2", "a2"))

    contents = [m["content"] for m in history.get("s1")]

    assert contents == ["hi", "hello", "q2", "a2"]
    assert history.exists("s1")


def test_limit_returns_latest_messages():
    history = InMemoryChatHistory()
    for i in range(5):
        history.add_messages("s1", turn(f"q{i}", f"a{i}"))

    contents = [m["content"] for m in history.get("s1", limit=3)]

    assert contents == ["a3", "q4", "a4"]
    assert history.get("s1", limit=0) == []


def test_max_messages_trims_old():
    history = InMemoryChatHistory(max_messages=4)
    for i in range(5):
        history.add_messages("s1", turn(f"q{i}", f"a{i}"))

    assert [m["content"] for m in history.get("s1")] == ["q3", "a3", "q4", "a4"]


def test_sessions_are_isolated():
    history = InMemoryChatHistory()
    history.add_messages("s1", turn("a", "b"))
    history.add_messages("s2", turn("c", "d"))

    assert [m["content"] for m in history.get("s1")] == ["a", "b"]
    assert [m["content"] for m in history.get("s2")] == ["c", "d"]


def test_clear():
    history = InMemoryChatHistory()
    history.add_messages("s1", turn("a", "b"))

    assert history.clear("s1") is True
    assert history.get("s1") == []
    assert history.clear("s1") is False


def test_get_returns_copy():
    history = InMemoryChatHistory()
    history.add_messages("s1", turn("a", "b"))

    history.get("s1")[0]["content"] = "changed"

    assert history.get("s1")[0]["content"] == "a"


def test_expired_session_is_gone():
    history = InMemoryChatHistory(cache=TTLCache(default_ttl=-1))
    history.add_messages("s1", turn("a", "b"))

    assert history.get("s1") == []
