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
    scored.sort(key=lambda x: x["score"], reverse=True)

    result.products = [item["product"] for item in scored[:top_k]]
    return result