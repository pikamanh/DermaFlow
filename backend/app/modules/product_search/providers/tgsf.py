import asyncio
import math

import httpx
from bs4 import BeautifulSoup

from backend.app.core.logging import setup_logger
from backend.app.modules.product_search.processors.detail_parser import (
    split_description_sections,
)
from backend.app.modules.product_search.providers.base import (
    ProductSearchProvider,
)
from backend.app.modules.product_search.schemas import (
    Product,
    ProductDetail,
    SearchQuery,
    SearchResult,
)


logger = setup_logger(__name__)


def _parse_product(data: dict, store_url: str) -> Product:
    price = int(data.get("price") or 0)
    compare = int(data.get("compare") or 0)
    market_price = compare if compare > price else price

    return Product(
        name=data["title"],
        brandName=data.get("vendor"),
        marketPrice=market_price,
        price=price,
        discountPercent=data.get("max_off"),
        categoryName=data.get("type"),
        urlProduct=f"{store_url}/products/{data['handle']}",
        source="tgsf",
    )


class TGSFProvider(ProductSearchProvider):
    PRODUCT_LIST_URL = "https://tgsf-search-prod-556171450242.asia-southeast1.run.app/api/search"

    async def search(self, search_query: SearchQuery) -> SearchResult:
        def build_params(page: int) -> dict:
            return {
                "q": search_query.query,
                "page": page,
            }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }

        def extract_in_stock(response_json: dict, store_url: str) -> list:
            products = response_json.get("products") or []
            return [
                _parse_product(product, store_url)
                for product in products
                if product.get("in_stock") is True
            ]

        try:
            async with httpx.AsyncClient(
                timeout=10.0,
            ) as client:
                first_response = await client.get(
                    url=self.PRODUCT_LIST_URL,
                    headers=headers,
                    params=build_params(1),
                )

                first_response.raise_for_status()
                response_json = first_response.json()
                store_url = "https://thegioiskinfood.com"

                list_in_stock = extract_in_stock(response_json, store_url)

                total_products = response_json.get("total", 0)
                per_page = response_json.get("per_page") or 1
                total_page = math.ceil(total_products / per_page)

                if total_page > 1:
                    other_responses = await asyncio.gather(
                        *[
                            client.get(
                                url=self.PRODUCT_LIST_URL,
                                headers=headers,
                                params=build_params(page),
                            )
                            for page in range(2, total_page + 1)
                        ]
                    )

                    for response in other_responses:
                        response.raise_for_status()
                        list_in_stock.extend(
                            extract_in_stock(response.json(), store_url)
                        )
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to search TGSF: {e}"
            )

            return SearchResult(
                query=search_query.query,
                products=[],
            )

        if not list_in_stock:
            logger.warning(
                "Cannot get data from TGSF."
            )

            return SearchResult(
                query=search_query.query,
                products=[],
            )

        logger.info(
            f"Get {len(list_in_stock)} products from TGSF."
        )

        return SearchResult(
            query=search_query.query,
            products=list_in_stock,
        )

    async def get_detail(self, url: str) -> ProductDetail | None:
        headers = {"User-Agent": "Mozilla/5.0"}
        json_url = url.rstrip("/") + ".json"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(json_url, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get TGSF detail for {url}: {e}")
            return None

        product = response.json().get("product")

        if not product:
            logger.warning(f"Cannot get detail from TGSF for {url}.")
            return None

        variant = (product.get("variants") or [{}])[0]
        price = int(variant.get("price") or 0)
        market_price = int(variant.get("compare_at_price") or 0)

        body_text = BeautifulSoup(
            product.get("body_html") or "", "html.parser"
        ).get_text("\n")

        description, ingredients, usage = split_description_sections(body_text)

        return ProductDetail(
            name=product["title"],
            brandName=product.get("vendor"),
            marketPrice=market_price or price,
            price=price,
            ingredients=ingredients,
            description=description or None,
            usage=usage,
            urlProduct=url,
            source="tgsf",
        )


async def main():
    tgsf = TGSFProvider()

    result = await tgsf.search(
        SearchQuery(query="kem chống nắng")
    )

    print(result.products[0] if result.products else "No products found")
    print(f"Total: {len(result.products or [])}")

    detail = await tgsf.get_detail(result.products[0].urlProduct)
    print(detail)


if __name__ == "__main__":
    asyncio.run(main())
