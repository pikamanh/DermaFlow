import asyncio
import time
import json

from...core.config import settings
from...core.logging import setup_logger

from .providers.base import ProductSearchProvider
from .providers.hasaki import HasakiProvider
from .providers.lamthao import LamThaoProvider
from .providers.tgsf import TGSFProvider

from .fallback.google import GoogleFallbackProvider

from .processors.normalizer import normalize
from .processors.deduplicator import deduplicate
from .processors.ranker import top_product

from .schemas import SearchQuery, SearchResult

logger = setup_logger(__name__)


class ProductSearchService:
    def __init__(self):
        self.providers = [
            HasakiProvider(),
            LamThaoProvider(),
            TGSFProvider(),
        ]
        self.fallback_provider = GoogleFallbackProvider()

    async def _search_with_latency(
        self,
        provider: ProductSearchProvider,
        search_query: SearchQuery,
    ) -> SearchResult:
        name = provider.__class__.__name__
        start = time.perf_counter()

        try:
            return await provider.search(search_query)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(f"Provider {name} took {elapsed_ms:.0f}ms")

    async def search(self, search_query: SearchQuery) -> SearchResult:
        start = time.perf_counter()

        #Get raw result
        results = await asyncio.gather(
            *[
                self._search_with_latency(provider, search_query)
                for provider in self.providers
            ],
            return_exceptions=True,
        )

        products = []

        for provider, result in zip(self.providers, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Provider {provider.__class__.__name__} failed: {result}"
                )
                continue

            products.extend(result.products or [])

        elapsed_ms = (time.perf_counter() - start) * 1000
        result = SearchResult(
            query=search_query.query,
            products=products,
        )
        logger.info(f"Total search took {elapsed_ms:.0f}ms")

        #Noramlize
        result_norm = normalize(result)

        #deduplicate
        result_deduplicate = deduplicate(result_norm)

        #Top K
        result_final = top_product(result_deduplicate)

        #Fallback nếu kết quả sau dedupe/rank vẫn quá ít
        if len(result_final.products or []) < settings.FALLBACK_MIN_RESULTS:
            result_final = await self._fallback_search(search_query, result_final)

        return result_final

    async def _fallback_search(
        self,
        search_query: SearchQuery,
        result_final: SearchResult,
    ) -> SearchResult:
        logger.warning(
            f"Fallback triggered for query='{search_query.query}' "
            f"(only {len(result_final.products or [])} results)"
        )

        try:
            fallback_result = await self.fallback_provider.search(search_query)
        except Exception as e:
            logger.error(f"Google fallback failed: {e}")
            return result_final

        if not fallback_result.products:
            return result_final

        merged = (result_final.products or []) + fallback_result.products

        merged_result = SearchResult(query=search_query.query, products=merged)
        merged_result = deduplicate(merged_result)
        merged_result = top_product(merged_result)

        return merged_result

async def main():
    search_services = ProductSearchService()

    result = await search_services.search(
        SearchQuery(query="kem chống nắng")
    )
    with open("backend/tests/test_product.json", "w", encoding="utf-8") as f:
        json.dump([product.model_dump() for product in result.products], f, indent=2, ensure_ascii=False)
    print(result.products[0] if result.products else "No products found")
    print(f"Total: {len(result.products or [])}")

if __name__ == "__main__":
    asyncio.run(main())