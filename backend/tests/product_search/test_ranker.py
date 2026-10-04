from backend.app.modules.product_search.processors.ranker import top_product
from backend.app.modules.product_search.schemas import Product, SearchResult


def _make_product(name: str, urlProduct: str, source: str = "hasaki") -> Product:
    return Product(
        name=name,
        marketPrice=100000,
        price=90000,
        urlProduct=urlProduct,
        source=source,
    )


def test_ranks_more_matching_tokens_first():
    products = [
        _make_product("Sữa Rửa Mặt ABC", "u1"),
        _make_product("Kem Chống Nắng Skin1004 50ml", "u2"),
        _make_product("Kem Chống Nắng ABC 50ml", "u3"),
    ]
    result = SearchResult(query="kem chống nắng skin1004", products=products)

    top_product(result, top_k=3)

    names = [p.name for p in result.products]
    assert names[0] == "Kem Chống Nắng Skin1004 50ml"
    assert names[-1] == "Sữa Rửa Mặt ABC"


def test_top_k_limits_result_count():
    products = [_make_product(f"Kem Chống Nắng {i}", f"u{i}") for i in range(10)]
    result = SearchResult(query="kem chống nắng", products=products)

    top_product(result, top_k=3)

    assert len(result.products) == 3


def test_matching_is_case_insensitive():
    products = [_make_product("KEM CHỐNG NẮNG ABC", "u1")]
    result = SearchResult(query="kem chống nắng", products=products)

    top_product(result, top_k=5)

    assert len(result.products) == 1


def test_top_k_applies_per_source_not_globally():
    # Hasaki có điểm cao hơn hẳn, nhưng LamThao/TGSF vẫn phải xuất hiện
    # trong kết quả cuối, không bị Hasaki chiếm hết top_k.
    products = [
        _make_product("Kem Chống Nắng A", "h1", source="hasaki"),
        _make_product("Kem Chống Nắng B", "h2", source="hasaki"),
        _make_product("Kem Chống Nắng C", "h3", source="hasaki"),
        _make_product("Kem Chống Nắng D", "l1", source="lamthao"),
        _make_product("Sữa Rửa Mặt E", "t1", source="tgsf"),
    ]
    result = SearchResult(query="kem chống nắng", products=products)

    top_product(result, top_k=2)

    sources = {p.source for p in result.products}
    assert sources == {"hasaki", "lamthao", "tgsf"}

    hasaki_count = sum(1 for p in result.products if p.source == "hasaki")
    assert hasaki_count == 2
