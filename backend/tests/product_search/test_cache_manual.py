"""
Test thủ công cho Cache ở tầng ProductSearchService (gọi 3 provider thật).

Chạy: make cache
"""

import asyncio
import time

from backend.app.modules.product_search.services import ProductSearchService
from backend.app.modules.product_search.schemas import SearchQuery


async def main():
    service = ProductSearchService()
    query = SearchQuery(query="kem chống nắng")

    start = time.perf_counter()
    result_1 = await service.search(query)
    elapsed_1 = (time.perf_counter() - start) * 1000
    print(f"Lần 1 (MISS): {elapsed_1:.0f}ms, {len(result_1.products or [])} products")

    start = time.perf_counter()
    result_2 = await service.search(query)
    elapsed_2 = (time.perf_counter() - start) * 1000
    print(f"Lần 2 (HIT):  {elapsed_2:.0f}ms, {len(result_2.products or [])} products")

    assert elapsed_2 < elapsed_1, "Cache HIT phải nhanh hơn MISS rõ rệt"
    assert result_1.products == result_2.products, "HIT phải trả đúng kết quả đã cache"

    print("OK: cache hoạt động đúng.")


if __name__ == "__main__":
    asyncio.run(main())
