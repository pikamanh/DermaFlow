from fastapi import APIRouter, HTTPException

from ...core.logging import setup_logger
from ...modules.chat.schemas import ChatRequest, HistoryResponse, Message, Response
from ...modules.chat.service import ChatService

logger = setup_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])
chatService = ChatService()


@router.post("", response_model=Response)
def chat(request: ChatRequest):
    try:
        return chatService.chat(request.query, request.session_id)
    except Exception:
        raise HTTPException(status_code=502, detail="LLM service unavailable")


@router.get("/{session_id}/history", response_model=HistoryResponse)
def get_history(session_id: str):
    if not chatService.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    messages = [Message(**m) for m in chatService.get_history(session_id)]
    return HistoryResponse(session_id=session_id, messages=messages)


@router.delete("/{session_id}/history", status_code=204)
def clear_history(session_id: str):
    if not chatService.clear_history(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
