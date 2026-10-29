from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    # Bỏ trống ở lượt đầu, server sẽ tạo session_id mới và trả về
    session_id: Optional[str] = Field(default=None, min_length=1, max_length=64)


class Response(BaseModel):
    session_id: str
    query: str
    response: Optional[str] = None


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: Optional[datetime] = None


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[Message]
