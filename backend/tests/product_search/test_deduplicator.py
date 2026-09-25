from backend.app.modules.product_search.processors.deduplicator import deduplicate
from backend.app.modules.product_search.schemas import Product, SearchResult


def _make_product(**overrides) -> Product:
    defaults = dict(
        name="Kem Chống Nắng ABC 50ml",
        brandName="ABC",
        volume="50ml",
        marketPrice=300000,
        price=250000,
        urlProduct="https://example.com/p1",
        source="hasaki",
    )
    defaults.update(overrides)
    return Product(**defaults)


def test_merges_same_brand_name_volume_across_sources():
    products = [
        _make_product(source="hasaki", marketPrice=300000, price=250000, urlProduct="u1"),
        _make_product(source="lamthao", marketPrice=280000, price=230000, urlProduct="u2"),
        _make_product(source="tgsf", marketPrice=310000, price=260000, urlProduct="u3"),
    ]
    result = SearchResult(query="q", products=products)

    deduplicate(result)

    assert len(result.products) == 1
    representative = result.products[0]
    assert representative.source == "lamthao"
    assert representative.marketPrice == 280000
    assert [s.source for s in representative.otherSource] == ["hasaki", "tgsf"]
    assert [s.marketPrice for s in representative.otherSource] == [300000, 310000]


def test_different_products_are_not_merged():
    products = [
        _make_product(name="Kem Chống Nắng ABC 50ml", urlProduct="u1"),
        _make_product(name="Kem Chống Nắng XYZ 50ml", urlProduct="u2"),
    ]
    result = SearchResult(query="q", products=products)

    deduplicate(result)

    assert len(result.products) == 2
    assert all(p.otherSource is None for p in result.products)


def test_products_without_volume_are_never_merged():
    products = [
        _make_product(name="Sữa Rửa Mặt ABC", volume=None, urlProduct="u1"),
        _make_product(name="Sữa Rửa Mặt ABC", volume=None, urlProduct="u2"),
    ]
    result = SearchResult(query="q", products=products)

    deduplicate(result)

    assert len(result.products) == 2
    assert all(p.otherSource is None for p in result.products)


def test_single_product_group_has_no_other_source():
    result = SearchResult(query="q", products=[_make_product()])

    deduplicate(result)

    assert len(result.products) == 1
    assert result.products[0].otherSource is None
