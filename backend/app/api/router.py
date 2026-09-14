from fastapi import APIRouter

from .v1.products import router as products_router

router = APIRouter()
router.include_router(router=products_router)

@router.get("/health")
async def health_check():
    return {
        "status": "ok"
    }