from abc import ABC, abstractmethod

from backend.app.modules.product_search.schemas import (
    ProductDetail,
    SearchQuery,
    SearchResult,
)

class ProductSearchProvider(ABC):
    @abstractmethod
    async def search(
        self,
        search_query: SearchQuery
    ) -> SearchResult:
        pass

    @abstractmethod
    async def get_detail(
        self,
        url: str,
    ) -> ProductDetail | None:
        pass