import pytest

from backend.app.modules.chat.service import ChatService
from backend.app.modules.chat.schemas import Response

@pytest.fixture
def service() -> ChatService:
    return ChatService()

def test_check_response(service):
    output = service.chat("Xin chào")

    assert output is not None
    assert isinstance(output, Response)

    print(output.response)
    
    assert len(output.response) > 1

def test_many_responses(service):
    queries = ["Xin chào", "Bạn là ai", "Đây là gì"]

    for query in queries:
        output = service.chat("Xin chào")
        
        assert output is not None
        assert isinstance(output, Response)
        
        assert len(output.response) > 1