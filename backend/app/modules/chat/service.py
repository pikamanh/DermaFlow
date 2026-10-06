from dotenv import load_dotenv
from openai import OpenAI
import os

from ...core.logging import setup_logger

load_dotenv()
logger = setup_logger(__name__)

class ChatService:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),
        )

    def chat(self, query: str):
        logger.info("Creating response.")
        try:
            completion = self.client.completions.create(
                model=str(os.getenv("MODEL")),
                messages=[
                    {
                        "role": "system",
                        "content": ""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            )
        except Exception as e:
            logger.error(e)

        logger.info("Created response successfully.")
        response = completion.choices[0].message.content

        return response

