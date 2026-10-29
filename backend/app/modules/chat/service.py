import os
from typing import Optional
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI

from ...core.logging import setup_logger
from .history import ChatHistory, InMemoryChatHistory
from .prompt import SYSTEM_PROMPT
from .schemas import Response

load_dotenv()
logger = setup_logger(__name__)

# Số message gần nhất gửi kèm cho LLM (10 lượt hỏi-đáp), tránh prompt phình to
MAX_HISTORY_MESSAGES = int(os.getenv("CHAT_MAX_HISTORY_MESSAGES", "20"))


def default_history() -> ChatHistory:
    from ...infastructure.database.session import is_database_configured

    if is_database_configured():
        from ...infastructure.database.history import DatabaseChatHistory

        return DatabaseChatHistory()

    logger.warning("DATABASE_URI is not set, chat history is stored in memory only.")
    return InMemoryChatHistory()


class ChatService:
    def __init__(
        self,
        history: Optional[ChatHistory] = None,
        client: Optional[OpenAI] = None,
        max_history_messages: int = MAX_HISTORY_MESSAGES,
    ):
        self.client = client or OpenAI(
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),
        )
        self.history = history or default_history()
        self.max_history_messages = max_history_messages
        self.model = str(os.getenv("MODEL"))

    def build_messages(self, query: str, session_id: str) -> list[dict]:
        history = self.history.get(session_id, limit=self.max_history_messages)

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            # Chỉ gửi role + content, bỏ created_at
            *({"role": m["role"], "content": m["content"]} for m in history),
            {"role": "user", "content": query},
        ]

    def chat(self, query: str, session_id: Optional[str] = None) -> Response:
        session_id = session_id or uuid4().hex
        logger.info(f"Creating response for session {session_id}.")

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.build_messages(query, session_id),
            )
        except Exception as e:
            logger.error(e)
            raise

        answer = completion.choices[0].message.content or ""
        logger.info("Created response successfully.")

        # Chỉ lưu khi LLM trả lời thành công, để history không bị lẻ message user
        self.history.add_messages(
            session_id,
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": answer},
            ],
        )

        return Response(session_id=session_id, query=query, response=answer)

    def get_history(self, session_id: str) -> list[dict]:
        return self.history.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        return self.history.exists(session_id)

    def clear_history(self, session_id: str) -> bool:
        return self.history.clear(session_id)
