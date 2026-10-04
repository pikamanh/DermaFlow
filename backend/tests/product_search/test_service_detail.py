from unittest.mock import AsyncMock

import pytest

from backend.app.modules.product_search.schemas import ProductDetail
from backend.app.modules.product_search.services import ProductSearchService


def _make_detail(source: str) -> ProductDetail:
    return ProductDetail(
        name="Kem chống nắng test",
        price=100000,
        urlProduct=f"https://{source}.example/product",
        source=source,
    )


@pytest.fixture
def service() -> ProductSearchService:
    return ProductSearchService()


@pytest.mark.asyncio
async def test_get_detail_routes_to_hasaki_provider(service):
    detail = _make_detail("hasaki")
    service.providers_by_source["hasaki"].get_detail = AsyncMock(
        return_value=detail
    )

    result = await service.get_detail(
        "https://hasaki.vn/san-pham/kem-chong-nang-183033.html"
    )

    assert result == detail
    service.providers_by_source["hasaki"].get_detail.assert_awaited_once_with(
        "https://hasaki.vn/san-pham/kem-chong-nang-183033.html"
    )


@pytest.mark.asyncio
async def test_get_detail_routes_to_lamthao_provider(service):
    detail = _make_detail("lamthao")
    service.providers_by_source["lamthao"].get_detail = AsyncMock(
        return_value=detail
    )

    result = await service.get_detail(
        "https://lamthaocosmetics.vn/products/kem-chong-nang"
    )

    assert result == detail
    service.providers_by_source["lamthao"].get_detail.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_detail_routes_to_tgsf_provider(service):
    detail = _make_detail("tgsf")
    service.providers_by_source["tgsf"].get_detail = AsyncMock(return_value=detail)

    result = await service.get_detail(
        "https://thegioiskinfood.com/products/kem-chong-nang"
    )

    assert result == detail
    service.providers_by_source["tgsf"].get_detail.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_detail_returns_none_for_unknown_domain(service):
    for provider in service.providers_by_source.values():
        provider.get_detail = AsyncMock()

    result = await service.get_detail("https://unknown-shop.vn/products/abc")

    assert result is None

    for provider in service.providers_by_source.values():
        provider.get_detail.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_detail_returns_none_when_provider_fails(service):
    service.providers_by_source["hasaki"].get_detail = AsyncMock(return_value=None)

    result = await service.get_detail(
        "https://hasaki.vn/san-pham/kem-chong-nang-183033.html"
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_detail_caches_result_and_skips_second_provider_call(service):
    detail = _make_detail("hasaki")
    mock_get_detail = AsyncMock(return_value=detail)
    service.providers_by_source["hasaki"].get_detail = mock_get_detail

    url = "https://hasaki.vn/san-pham/kem-chong-nang-183033.html"

    first = await service.get_detail(url)
    second = await service.get_detail(url)

    assert first == detail
    assert second == detail
    mock_get_detail.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_detail_does_not_cache_none_result(service):
    mock_get_detail = AsyncMock(return_value=None)
    service.providers_by_source["hasaki"].get_detail = mock_get_detail

    url = "https://hasaki.vn/san-pham/kem-chong-nang-183033.html"

    await service.get_detail(url)
    await service.get_detail(url)

    assert mock_get_detail.await_count == 2
