from fastapi import APIRouter, HTTPException

from ...modules.product_search.schemas import ProductDetail, SearchQuery, SearchResult
from ...modules.product_search.services import ProductSearchService

from ...modules.chat.service import ChatService

router = APIRouter(prefix="/products")
services = ProductSearchService()
chatService = ChatService()

@router.get("/search", response_model=SearchResult)
async def search_products(query: str) -> SearchResult:
    search_query = SearchQuery(query=query)
    return await services.search(search_query)

@router.get("/detail", response_model=ProductDetail)
async def get_product_detail(url: str) -> ProductDetail:
    detail = await services.get_detail(url)

    if detail is None:
        raise HTTPException(status_code=404, detail="Product detail not found")

    return detail

@router.get("/chat")
async def chat(query: str) -> str:
    return await chatService.chat(query)