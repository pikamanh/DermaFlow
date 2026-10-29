from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.router import router
from backend.app.core.logging import setup_logger
from backend.app.infastructure.database.session import close_db, init_db, is_database_configured

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if is_database_configured():
        init_db()

    yield

    close_db()


app = FastAPI(
    title="DermaFlow API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
