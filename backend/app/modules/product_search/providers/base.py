from abc import ABC, abstractmethod

from backend.app.modules.product_search.schemas import SearchQuery, SearchResult

class ProductSearchProvider(ABC):
    @abstractmethod
    async def search(
        self,
        search_query: SearchQuery
    ) -> SearchResult:
        pass