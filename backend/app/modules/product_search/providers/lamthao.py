import asyncio
import re

import httpx
from bs4 import BeautifulSoup

from backend.app.core.logging import setup_logger
from backend.app.modules.product_search.providers.base import (
    ProductSearchProvider,
)
from backend.app.modules.product_search.schemas import (
    Product,
    SearchQuery,
    SearchResult,
)


logger = setup_logger(__name__)


def _parse_price(text: str) -> int:
    digits = re.sub(r"\D", "", text or "")
    return int(digits) if digits else 0


def _parse_products(html: str, site_url: str) -> list[Product]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select(".product-loop"):
        title_tag = item.select_one("h3.titleproduct a")
        price_tag = item.select_one(".proloop--priceflex .price")

        if not title_tag or not price_tag:
            continue

        name = title_tag.get_text(strip=True)
        url_product = site_url + title_tag["href"]

        vendor_tag = item.select_one(".feevendor")
        brand_name = vendor_tag.get_text(strip=True) if vendor_tag else None

        price = _parse_price(price_tag.get_text())

        del_tag = item.select_one(".proloop--priceflex .price-del")
        market_price = _parse_price(del_tag.get_text()) if del_tag else price

        sale_tag = item.select_one(".pro-sale span")
        discount_percent = (
            abs(_parse_price(sale_tag.get_text()))
            if sale_tag
            else (
                round((1 - price / market_price) * 100, 2)
                if market_price and market_price != price
                else None
            )
        )

        products.append(
            Product(
                name=name,
                brandName=brand_name,
                marketPrice=market_price,
                price=price,
                discountPercent=discount_percent,
                urlProduct=url_product,
                source="lamthao",
            )
        )

    return products


def _parse_last_page(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    page_numbers = [0]

    for link in soup.select("#pagination a[href]"):
        match = re.search(r"page=(\d+)", link["href"])

        if match:
            page_numbers.append(int(match.group(1)))

    return max(page_numbers) or 1


class LamThaoProvider(ProductSearchProvider):
    BASE_URL = "https://lamthaocosmetics.vn/search"
    SITE_URL = "https://lamthaocosmetics.vn"
    MAX_PAGES = 5

    async def search(
        self,
        search_query: SearchQuery,
    ) -> SearchResult:
        headers = {
            "User-Agent": "Mozilla/5.0",
        }

        def build_params(page: int) -> dict:
            return {
                "q": f"filter=(title:product contains {search_query.query})",
                "page": page,
            }

        try:
            async with httpx.AsyncClient(
                timeout=10.0,
            ) as client:
                first_response = await client.get(
                    url=self.BASE_URL,
                    params=build_params(1),
                    headers=headers,
                )

                first_response.raise_for_status()

                pages_html = [first_response.text]

                last_page = min(
                    _parse_last_page(first_response.text),
                    self.MAX_PAGES,
                )

                if last_page > 1:
                    other_responses = await asyncio.gather(
                        *[
                            client.get(
                                url=self.BASE_URL,
                                params=build_params(page),
                                headers=headers,
                            )
                            for page in range(2, last_page + 1)
                        ]
                    )

                    for response in other_responses:
                        response.raise_for_status()
                        pages_html.append(response.text)
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to search LamThao: {e}"
            )

            return SearchResult(
                query=search_query.query,
                products=[],
            )

        products = [
            product
            for html in pages_html
            for product in _parse_products(html, self.SITE_URL)
        ]

        if not products:
            logger.warning(
                "Cannot get data from LamThao."
            )

            return SearchResult(
                query=search_query.query,
                products=[],
            )

        logger.info(
            f"Get {len(products)} products from LamThao."
        )

        return SearchResult(
            query=search_query.query,
            products=products,
        )


async def main():
    lamthao = LamThaoProvider()

    result = await lamthao.search(
        SearchQuery(query="kem chống nắng")
    )

    print(result.products[0] if result.products else "No products found")
    print(f"Total: {len(result.products or [])}")


if __name__ == "__main__":
    asyncio.run(main())
