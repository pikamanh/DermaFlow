from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from ...core.logging import setup_logger
from .models import ChatMessage, ChatSession
from .session import get_session_factory

logger = setup_logger(__name__)


def _to_dict(message: ChatMessage) -> dict:
    return {
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
    }


class DatabaseChatHistory:
    """Lưu history chat vào PostgreSQL (Neon). Cùng interface với InMemoryChatHistory."""

    def __init__(self, session_factory: Optional[sessionmaker[Session]] = None):
        self._session_factory = session_factory or get_session_factory()

    def get(self, session_id: str, limit: Optional[int] = None) -> list[dict]:
        """Lấy message theo thứ tự cũ → mới. limit = chỉ lấy N message gần nhất."""
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id)

        with self._session_factory() as db:
            if limit is None:
                rows = db.scalars(stmt.order_by(ChatMessage.id)).all()
            else:
                rows = db.scalars(stmt.order_by(ChatMessage.id.desc()).limit(limit)).all()
                rows = list(reversed(rows))

            return [_to_dict(row) for row in rows]

    def add_messages(self, session_id: str, messages: list[dict]) -> None:
        """Ghi nhiều message trong 1 transaction (user + assistant của cùng 1 lượt)."""
        with self._session_factory.begin() as db:
            chat_session = db.get(ChatSession, session_id)

            if chat_session is None:
                chat_session = ChatSession(id=session_id)
                db.add(chat_session)
                # Đảm bảo session tồn tại trước khi insert message (FK)
                db.flush()

            for message in messages:
                db.add(ChatMessage(session_id=session_id, role=message["role"], content=message["content"]))

            chat_session.updated_at = func.now()

    def exists(self, session_id: str) -> bool:
        with self._session_factory() as db:
            return db.get(ChatSession, session_id) is not None

    def clear(self, session_id: str) -> bool:
        """Xoá session và toàn bộ message. Trả về False nếu session không tồn tại."""
        with self._session_factory.begin() as db:
            result = db.execute(delete(ChatSession).where(ChatSession.id == session_id))

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted chat session {session_id}.")

        return deleted
