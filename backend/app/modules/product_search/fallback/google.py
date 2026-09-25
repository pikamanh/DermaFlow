import asyncio
import json

import httpx
from bs4 import BeautifulSoup

from backend.app.core.config import settings
from backend.app.core.logging import setup_logger
from backend.app.modules.product_search.schemas import (
    Product,
    SearchQuery,
    SearchResult,
)


logger = setup_logger(__name__)

# Domain đã biết cấu trúc site -> source name (khớp với các provider hiện có).
# TGSF không có ở đây vì domain của nó là Shopify store, lấy động từ API,
# không cố định để match URL Google trả về.
KNOWN_DOMAINS = {
    "hasaki.vn": "hasaki",
    "lamthaocosmetics.vn": "lamthao",
}


def _match_source(url: str) -> str | None:
    for domain, source in KNOWN_DOMAINS.items():
        if domain in url:
            return source
    return None


def _extract_product_from_jsonld(html: str, url: str, source: str) -> Product | None:
    """
    Lấy tối thiểu name/price từ JSON-LD schema.org Product, đủ để lấp Product
    schema. Đây là bản tối giản, sẽ được thay bằng detail fetch đầy đủ ở
    Phase 7 (Product Detail).
    """
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        candidates = data if isinstance(data, list) else [data]

        for item in candidates:
            if not isinstance(item, dict):
                continue
            if item.get("@type") != "Product":
                continue

            name = item.get("name")
            offers = item.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            price_raw = offers.get("price")
            if not name or price_raw is None:
                continue

            try:
                price = int(float(price_raw))
            except (TypeError, ValueError):
                continue

            return Product(
                name=name,
                marketPrice=price,
                price=price,
                urlProduct=url,
                source=source,
            )

    return None


class GoogleFallbackProvider:
    SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

    async def search(self, search_query: SearchQuery) -> SearchResult:
        if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
            logger.error(
                "Google fallback chưa được cấu hình (thiếu GOOGLE_API_KEY/GOOGLE_CSE_ID)."
            )
            return SearchResult(query=search_query.query, products=[])

        params = {
            "key": settings.GOOGLE_API_KEY,
            "cx": settings.GOOGLE_CSE_ID,
            "q": search_query.query,
            "num": 10,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.SEARCH_URL, params=params)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Google fallback search failed: {e} | body: {e.response.text}"
            )
            return SearchResult(query=search_query.query, products=[])
        except httpx.HTTPError as e:
            logger.error(f"Google fallback search failed: {e}")
            return SearchResult(query=search_query.query, products=[])

        items = response.json().get("items") or []

        if not items:
            logger.warning(f"Google fallback: no results for '{search_query.query}'.")
            return SearchResult(query=search_query.query, products=[])

        # Chỉ giữ link thuộc domain đã biết (lựa chọn A), bỏ qua domain lạ.
        matched = [
            (item["link"], source)
            for item in items
            if item.get("link") and (source := _match_source(item["link"]))
        ]

        if not matched:
            logger.warning(
                f"Google fallback: no known-domain result for '{search_query.query}'."
            )
            return SearchResult(query=search_query.query, products=[])

        products = await asyncio.gather(
            *[self._fetch_detail(url, source) for url, source in matched],
            return_exceptions=True,
        )

        valid_products = [
            product
            for product in products
            if isinstance(product, Product)
        ]

        logger.info(
            f"Google fallback matched {len(valid_products)}/{len(matched)} known-domain products."
        )

        return SearchResult(query=search_query.query, products=valid_products)

    async def _fetch_detail(self, url: str, source: str) -> Product | None:
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Google fallback: failed to fetch detail {url}: {e}")
            return None

        product = _extract_product_from_jsonld(response.text, url, source)

        if not product:
            logger.warning(f"Google fallback: no JSON-LD product data at {url}.")

        return product


async def main():
    google = GoogleFallbackProvider()

    result = await google.search(SearchQuery(query="kem chống nắng"))

    print(result.products[0] if result.products else "No products found")
    print(f"Total: {len(result.products or [])}")


if __name__ == "__main__":
    asyncio.run(main())
