from fastapi import APIRouter, HTTPException

from ...modules.chat.service import ChatService
from ...modules.chat.schemas import Response

router = APIRouter(prefix="/chat")
chatService = ChatService()

@router.get("", response_model=Response)
def chat(query: str):
    try:
        return chatService.chat(query)
    except Exception:
        raise HTTPException(status_code=502, detail="LLM service unavailable")