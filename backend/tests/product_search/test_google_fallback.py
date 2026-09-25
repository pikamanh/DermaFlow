"""
Test thủ công cho Google Fallback.

Chạy: python scripts/test_google_fallback.py "<query hiếm để ép fallback>"
"""

import asyncio
import sys

from backend.app.modules.product_search.fallback.google import GoogleFallbackProvider
from backend.app.modules.product_search.schemas import SearchQuery


async def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "kem chống nắng"

    fallback = GoogleFallbackProvider()
    result = await fallback.search(SearchQuery(query=query))

    print(f"Query: {query}")
    print(f"Total fallback products: {len(result.products or [])}")

    for product in result.products or []:
        print(f"- [{product.source}] {product.name} - {product.price}đ - {product.urlProduct}")


if __name__ == "__main__":
    asyncio.run(main())
