from backend.app.modules.product_search.processors.normalizer import normalize
from backend.app.modules.product_search.schemas import Product, SearchResult


def _make_product(**overrides) -> Product:
    defaults = dict(
        name="  Kem   Chống  Nắng ABC 50ml ",
        englishName=None,
        brandName=None,
        volume=None,
        marketPrice=100000,
        price=90000,
        urlProduct="https://example.com/p1",
        source="hasaki",
    )
    defaults.update(overrides)
    return Product(**defaults)


def test_collapses_internal_and_trailing_whitespace():
    result = SearchResult(query="q", products=[_make_product()])

    normalize(result)

    assert result.products[0].name == "Kem Chống Nắng ABC 50ml"


def test_none_optional_text_fields_stay_none():
    product = _make_product(englishName=None, brandName=None, categoryName=None)
    result = SearchResult(query="q", products=[product])

    normalize(result)

    assert result.products[0].englishName is None
    assert result.products[0].brandName is None


def test_blank_optional_text_becomes_none():
    product = _make_product(englishName="   ")
    result = SearchResult(query="q", products=[product])

    normalize(result)

    assert result.products[0].englishName is None


def test_negative_prices_are_clamped_to_zero():
    product = _make_product(marketPrice=-5000, price=-1000)
    result = SearchResult(query="q", products=[product])

    normalize(result)

    assert result.products[0].marketPrice == 0
    assert result.products[0].price == 0


def test_extracts_volume_from_name():
    product = _make_product(name="Kem Chống Nắng ABC 50ml", volume=None)
    result = SearchResult(query="q", products=[product])

    normalize(result)

    assert result.products[0].volume == "50ml"


def test_volume_stays_none_when_not_present_in_name():
    product = _make_product(name="Sữa Rửa Mặt XYZ", volume=None)
    result = SearchResult(query="q", products=[product])

    normalize(result)

    assert result.products[0].volume is None
