import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")
    FALLBACK_MIN_RESULTS: int = int(os.getenv("FALLBACK_MIN_RESULTS", "3"))


settings = Settings()
