"""
Test với LLM thật (tốn API call). Chạy riêng bằng: make test-llm
History lưu in-memory để không ghi rác vào database.
"""
import pytest

from backend.app.modules.chat.history import InMemoryChatHistory
from backend.app.modules.chat.schemas import Response
from backend.app.modules.chat.service import ChatService

pytestmark = pytest.mark.llm


@pytest.fixture
def service() -> ChatService:
    return ChatService(history=InMemoryChatHistory())


def test_check_response(service):
    output = service.chat("Xin chào")

    assert isinstance(output, Response)
    print(output.response)

    assert output.response and len(output.response) > 1


def test_many_responses(service):
    queries = ["Xin chào", "Bạn là ai", "Da dầu nên dùng sữa rửa mặt như thế nào?"]
    session_id = None

    for query in queries:
        output = service.chat(query, session_id)
        session_id = output.session_id

        assert isinstance(output, Response)
        assert output.response and len(output.response) > 1
        print(f"\n> {query}\n{output.response}")

    assert len(service.get_history(session_id)) == 2 * len(queries)


def test_remembers_previous_turn(service):
    first = service.chat("Tôi tên là Minh và da tôi là da dầu. Hãy ghi nhớ nhé.")
    output = service.chat("Tôi tên là gì và da tôi thuộc loại nào?", first.session_id)

    print(output.response)

    assert "Minh" in output.response
    assert "dầu" in output.response.lower()
