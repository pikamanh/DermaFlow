from dotenv import load_dotenv
from openai import OpenAI
import os

from ...core.logging import setup_logger
from ..cache import TTLCache
from .schemas import Response
from .history import ChatHistory
from .prompt import SYSTEM_PROMPT

load_dotenv()
logger = setup_logger(__name__)

class ChatService:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),
        )
        self.history = ChatHistory(cache=TTLCache(default_ttl=1800))

    def chat(self, query: str, session_id: str) -> Response:
        logger.info("Creating response.")
        try:
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ]
            messages.append(self.history.get(session_id))
            messages.append({
                "role": "user",
                "content": query
            })
            completion = self.client.chat.completions.create(
                model=str(os.getenv("MODEL")),
                messages=messages
            )
        except Exception as e:
            logger.error(e)
            raise

        logger.info("Created response successfully.")

        self.history.append(session_id, "user", query)
        self.history.append(session_id, "assistant", completion.choices[0].message.content)

        return Response(
            query=query,
            response=completion.choices[0].message.content
        )