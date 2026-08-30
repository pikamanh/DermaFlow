import httpx

from backend.app.core.logging import setup_logger
from backend.app.modules.product_search.providers.base import (
    ProductSearchProvider,
)
from backend.app.modules.product_search.schemas import (
    parse_product,
    SearchQuery,
    SearchResult,
)


logger = setup_logger(__name__)


class HasakiProvider(ProductSearchProvider):
    BASE_URL = "https://hasaki.vn/api/v4/main/query"
    PRODUCT_LIST_URL = "https://hasaki.vn/mobile/v3/main/products"

    async def search(
        self,
        search_query: SearchQuery,
    ) -> SearchResult:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=10.0,
            ) as client:

                query_response = await client.get(
                    url=self.BASE_URL,
                    params={"q": search_query.query},
                    headers=headers,
                )

                query_response.raise_for_status()

                url_data = query_response.json().get("data").get("url")

                product_response = await client.get(
                    url=self.PRODUCT_LIST_URL,
                    params={
                        "cate_path": url_data.split(".html")[0].split("/")[-1],
                        "page": 1,
                        "size": 60,
                        "has_meta_data": 1,
                        "is_desktop": 1
                    },
                    headers=headers
                )

                product_response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to search Hasaki: {e}"
            )

            return SearchResult(
                query=search_query.query,
                products=[],
            )

        raw_products = product_response.json().get("data").get("products")

        if not raw_products:
            logger.warning(
                "Cannot get data from Hasaki."
            )

            return SearchResult(
                query=search_query.query,
                products=[],
            )

        logger.info(
            f"Get {len(raw_products)} products from Hasaki."
        )

        products = [
            parse_product(product, "hasaki")
            for product in raw_products
        ]

        return SearchResult(
            query=search_query.query,
            products=products,
        )

async def main():
    hasaki = HasakiProvider()

    result = await hasaki.search(
        SearchQuery(query="kem chống nắng")
    )

    print(result.products[0])


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())