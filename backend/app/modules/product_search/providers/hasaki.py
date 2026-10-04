import json
import re

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from backend.app.core.logging import setup_logger
from backend.app.modules.product_search.providers.base import (
    ProductSearchProvider,
)
from backend.app.modules.product_search.schemas import (
    parse_product,
    ProductDetail,
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

    async def get_detail(self, url: str) -> ProductDetail | None:
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch()

                try:
                    page = await browser.new_page(user_agent=headers["User-Agent"])
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    html = await page.content()
                finally:
                    await browser.close()
        except Exception as e:
            logger.error(f"Failed to render Hasaki detail for {url}: {e}")
            return None

        soup = BeautifulSoup(html, "html.parser")

        ld_json = None
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.get_text())
            except json.JSONDecodeError:
                continue

            if data.get("@type") == "Product":
                ld_json = data
                break

        if not ld_json:
            logger.warning(f"Cannot get detail from Hasaki for {url}.")
            return None

        def section_text(element_id: str) -> str | None:
            node = soup.find(id=element_id)
            return node.get_text(" ", strip=True) if node else None

        description = section_text("DescriptionInfo")
        usage = section_text("GuideInfo")

        ingredients = None
        ingredient_text = section_text("IngredientInfo")

        if ingredient_text:
            detail_match = re.search(
                r"Thành phần chi tiết\s*:\s*(.+)", ingredient_text
            )
            chunk = detail_match.group(1) if detail_match else ingredient_text
            ingredients = [
                item.strip() for item in chunk.split(",") if item.strip()
            ] or None

        offer = ld_json.get("offers") or {}

        return ProductDetail(
            name=ld_json.get("name"),
            brandName=(ld_json.get("brand") or {}).get("name"),
            price=int(offer.get("price") or 0),
            ingredients=ingredients,
            description=description,
            usage=usage,
            urlProduct=url,
            source="hasaki",
        )


async def main():
    hasaki = HasakiProvider()

    result = await hasaki.search(
        SearchQuery(query="kem chống nắng")
    )

    print(result.products[0])

    detail = await hasaki.get_detail(result.products[0].urlProduct)
    print(detail)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())