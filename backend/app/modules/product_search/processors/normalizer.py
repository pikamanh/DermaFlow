import re
import json

from ..schemas import Product, SearchResult

_WHITESPACE_RE = re.compile(r"\s+")
_VOLUME_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|g|kg|ml|l)\b")


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = _WHITESPACE_RE.sub(" ", value).strip()
    return cleaned or None

def _seperate_volume(value: str | None) -> str | None:
    if value is None:
        return None
    
    volume = _VOLUME_RE.findall(value)
    if volume:
        return volume[0]
    else:
        return None
        

def _normalize_product(product: Product) -> None:
    product.name = _clean_text(product.name) or product.name
    product.englishName = _clean_text(product.englishName)
    product.brandName = _clean_text(product.brandName)
    product.categoryName = _clean_text(product.categoryName)

    product.marketPrice = max(product.marketPrice, 0)
    product.price = max(product.price, 0)

    product.volume = _seperate_volume(product.name)


def normalize(result: SearchResult) -> SearchResult:
    for product in result.products or []:
        _normalize_product(product)

    return result

if __name__ == "__main__":
    with open("backend/tests/test_product.json", "r") as f:
        result = SearchResult(query="Test", products=json.load(f))

    result_norm = normalize(result)
    print(result_norm.products[0])