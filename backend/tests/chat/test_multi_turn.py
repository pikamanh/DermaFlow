"""Test nhiều lượt chat với LLM giả: không gọi mạng, chạy nhanh."""
import pytest
from fastapi.testclient import TestClient

from backend.app.api.v1 import chat as chat_api
from backend.app.main import app
from backend.app.modules.chat.history import InMemoryChatHistory
from backend.app.modules.chat.prompt import SYSTEM_PROMPT
from backend.app.modules.chat.service import ChatService

from backend.tests.chat.fakes import FakeLLMClient


@pytest.fixture
def llm() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def service(llm) -> ChatService:
    return ChatService(history=InMemoryChatHistory(), client=llm)


def test_first_turn_creates_session(service, llm):
    output = service.chat("Xin chào")

    assert output.session_id
    assert output.response == "answer 1"
    assert llm.calls[0] == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Xin chào"},
    ]


def test_second_turn_sends_previous_history(service, llm):
    first = service.chat("Da tôi là da dầu")
    service.chat("Nên dùng sữa rửa mặt nào?", first.session_id)

    sent = llm.calls[1]

    # Mỗi message là 1 dict phẳng, không phải list lồng nhau
    assert all(isinstance(m, dict) for m in sent)
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]
    assert sent[1]["content"] == "Da tôi là da dầu"
    assert sent[2]["content"] == "answer 1"
    assert sent[3]["content"] == "Nên dùng sữa rửa mặt nào?"


def test_many_turns_keep_order(service, llm):
    queries = ["Xin chào", "Bạn là ai", "Da khô nên làm gì", "Cảm ơn"]
    session_id = None

    for query in queries:
        session_id = service.chat(query, session_id).session_id

    history = service.get_history(session_id)

    assert len(history) == 2 * len(queries)
    assert [m["content"] for m in history if m["role"] == "user"] == queries
    # Lượt cuối gửi đủ 3 lượt trước (6 message) + system + câu hỏi mới
    assert len(llm.calls[-1]) == 1 + 6 + 1


def test_sessions_do_not_leak(service, llm):
    a = service.chat("Tôi tên An")
    b = service.chat("Tôi tên Bình")
    service.chat("Tôi tên gì?", a.session_id)

    contents = [m["content"] for m in llm.calls[-1]]

    assert a.session_id != b.session_id
    assert "Tôi tên An" in contents
    assert "Tôi tên Bình" not in contents


def test_history_window_is_limited(llm):
    service = ChatService(history=InMemoryChatHistory(), client=llm, max_history_messages=4)
    session_id = None

    for i in range(5):
        session_id = service.chat(f"q{i}", session_id).session_id

    # system + 4 message gần nhất + câu hỏi mới
    sent = llm.calls[-1]
    assert len(sent) == 6
    assert [m["content"] for m in sent[1:]] == ["q2", "answer 3", "q3", "answer 4", "q4"]


def test_failed_llm_call_does_not_save_history():
    service = ChatService(history=InMemoryChatHistory(), client=FakeLLMClient(fail=True))

    with pytest.raises(RuntimeError):
        service.chat("Xin chào", "s1")

    assert service.get_history("s1") == []


# ---------- API ----------

@pytest.fixture
def client(monkeypatch, llm):
    monkeypatch.setattr(
        chat_api, "chatService", ChatService(history=InMemoryChatHistory(), client=llm)
    )
    # Không dùng "with TestClient(...)" để bỏ qua lifespan (không kết nối Neon)
    return TestClient(app)


def test_api_multi_turn_flow(client):
    first = client.post("/v1/chat", json={"query": "Xin chào"})
    assert first.status_code == 200
    session_id = first.json()["session_id"]

    second = client.post("/v1/chat", json={"query": "Da dầu dùng gì?", "session_id": session_id})
    assert second.status_code == 200
    assert second.json()["session_id"] == session_id

    history = client.get(f"/v1/chat/{session_id}/history")
    assert history.status_code == 200
    assert [m["content"] for m in history.json()["messages"]] == [
        "Xin chào", "answer 1", "Da dầu dùng gì?", "answer 2",
    ]

    assert client.delete(f"/v1/chat/{session_id}/history").status_code == 204
    assert client.get(f"/v1/chat/{session_id}/history").status_code == 404
    assert client.delete(f"/v1/chat/{session_id}/history").status_code == 404


def test_api_rejects_empty_query(client):
    assert client.post("/v1/chat", json={"query": ""}).status_code == 422


def test_api_llm_error_returns_502(monkeypatch):
    monkeypatch.setattr(
        chat_api,
        "chatService",
        ChatService(history=InMemoryChatHistory(), client=FakeLLMClient(fail=True)),
    )

    response = TestClient(app).post("/v1/chat", json={"query": "Xin chào"})

    assert response.status_code == 502
