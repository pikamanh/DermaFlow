import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ...core.logging import setup_logger
from .models import Base

load_dotenv()
logger = setup_logger(__name__)


def build_database_url(raw_url: str) -> str:
    """
    Neon trả về URI dạng postgresql://...?sslmode=require&channel_binding=require.
    Đổi sang driver psycopg (v3) để SQLAlchemy dùng; psycopg hiểu luôn sslmode
    và channel_binding nên không cần sửa query string.
    """
    for prefix in ("postgresql://", "postgres://"):
        if raw_url.startswith(prefix):
            return "postgresql+psycopg://" + raw_url[len(prefix):]

    return raw_url


def create_db_engine(raw_url: str) -> Engine:
    return create_engine(
        build_database_url(raw_url),
        # Neon tự suspend compute khi rảnh, connection cũ có thể đã chết
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=5,
    )


_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker[Session]] = None


def is_database_configured() -> bool:
    return bool(os.getenv("DATABASE_URI"))


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        raw_url = os.getenv("DATABASE_URI")

        if not raw_url:
            raise RuntimeError("DATABASE_URI is not set")

        _engine = create_db_engine(raw_url)

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)

    return _session_factory


def init_db() -> None:
    """Tạo bảng nếu chưa có. Gọi 1 lần lúc backend khởi động."""
    Base.metadata.create_all(get_engine())
    logger.info("Database tables are ready.")


def close_db() -> None:
    global _engine, _session_factory

    if _engine is not None:
        _engine.dispose()

    _engine = None
    _session_factory = None
