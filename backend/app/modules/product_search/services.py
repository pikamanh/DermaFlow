from .providers.hasaki import HasakiProvider
from .schemas import SearchQuery, SearchResult

class ProductSearchService:
    def __init__(self):
        self.hasaki_provider = HasakiProvider()

    async def search(self, search_query: SearchQuery) -> SearchResult:
        return await self.hasaki_provider.search(search_query)