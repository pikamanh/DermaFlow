from ..schemas import Product, SearchResult

def _tokenize(text: str) -> list[str]:
    return text.lower().split()

def _relevance_score(product: Product, query_tokens: list[str]) -> int:
    name_tokens = _tokenize(product.name)
    return sum(1 for token in query_tokens if token in name_tokens)

def top_product(result: SearchResult, top_k: int = 5) -> SearchResult:
    query_tokens = _tokenize(result.query)

    scored = [
        {"product": product, "score": _relevance_score(product, query_tokens)}
        for product in result.products or []
    ]

    # Gom theo source để mỗi provider đều có đại diện trong kết quả,
    # tránh trường hợp 1 provider điểm cao chiếm hết top_k.
    by_source: dict[str, list[dict]] = {}
    for item in scored:
        by_source.setdefault(item["product"].source, []).append(item)

    top_products: list[Product] = []
    for source_items in by_source.values():
        source_items.sort(key=lambda x: x["score"], reverse=True)
        top_products.extend(item["product"] for item in source_items[:top_k])

    result.products = top_products
    return result