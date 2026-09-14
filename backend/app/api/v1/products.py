from fastapi import APIRouter

from ...modules.product_search.schemas import SearchQuery, SearchResult
from ...modules.product_search.services import ProductSearchService

router = APIRouter(prefix="/products")
services = ProductSearchService()

@router.get("/search", response_model=SearchResult)
async def search_products(query: str) -> SearchResult:
    search_query = SearchQuery(query=query)
    return await services.search(search_query)