from fastapi import FastAPI

from backend.app.api.router import router

app = FastAPI(
    title="DermaFlow API",
    version="0.1.0",
)

app.include_router(router)