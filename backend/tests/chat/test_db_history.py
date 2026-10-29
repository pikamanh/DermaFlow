"""
Integration test với database thật (Neon). Tự skip nếu chưa có DATABASE_URI.
Mỗi test dùng session_id riêng và tự xoá dữ liệu sau khi chạy.
"""
from uuid import uuid4

import pytest

from backend.app.infastructure.database.session import build_database_url, is_database_configured

from backend.tests.chat.fakes import FakeLLMClient


def test_build_database_url():
    assert build_database_url("postgresql://u:p@h/db?sslmode=require").startswith("postgresql+psycopg://")
    assert build_database_url("postgres://u:p@h/db").startswith("postgresql+psycopg://")
    assert build_database_url("sqlite://") == "sqlite://"


@pytest.fixture(scope="module")
def history():
    from backend.app.infastructure.database.history import DatabaseChatHistory
    from backend.app.infastructure.database.session import close_db, init_db

    init_db()
    yield DatabaseChatHistory()
    close_db()


@pytest.fixture
def session_id(history):
    sid = f"test-{uuid4().hex}"
    yield sid
    history.clear(sid)


@pytest.mark.db
@pytest.mark.skipif(not is_database_configured(), reason="DATABASE_URI is not set")
def test_add_get_clear(history, session_id):
    assert history.exists(session_id) is False
    assert history.get(session_id) == []

    history.add_messages(session_id, [
        {"role": "user", "content": "Xin chào"},
        {"role": "assistant", "content": "Chào bạn"},
    ])
    history.add_messages(session_id, [
        {"role": "user", "content": "Da dầu"},
        {"role": "assistant", "content": "Ok"},
    ])

    messages = history.get(session_id)

    assert history.exists(session_id)
    assert [m["content"] for m in messages] == ["Xin chào", "Chào bạn", "Da dầu", "Ok"]
    assert messages[0]["created_at"] is not None
    assert [m["content"] for m in history.get(session_id, limit=2)] == ["Da dầu", "Ok"]

    assert history.clear(session_id) is True
    assert history.get(session_id) == []
    assert history.clear(session_id) is False


@pytest.mark.db
@pytest.mark.skipif(not is_database_configured(), reason="DATABASE_URI is not set")
def test_multi_turn_with_database(history, session_id):
    from backend.app.modules.chat.service import ChatService

    llm = FakeLLMClient()
    service = ChatService(history=history, client=llm)

    for query in ["Xin chào", "Da tôi bị mụn", "Nên dùng BHA không?"]:
        service.chat(query, session_id)

    assert len(history.get(session_id)) == 6
    assert [m["role"] for m in llm.calls[-1]] == [
        "system", "user", "assistant", "user", "assistant", "user",
    ]
