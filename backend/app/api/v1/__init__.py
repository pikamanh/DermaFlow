from fastapi import APIRouter

from .products import router as product_router
from .chat import router as chat_router

router = APIRouter(prefix="/v1")

router.include_router(product_router)
router.include_router(chat_router)