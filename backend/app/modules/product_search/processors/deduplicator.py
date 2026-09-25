from ..schemas import Product, SearchResult, ProductSource

def _group_key(product: Product) -> tuple | None:
    if product.volume is None:
        return None

    return (
        product.name.lower(),
        product.brandName.lower() if product.brandName is not None else None,
        product.volume
        )

def _group_product(result: SearchResult) -> tuple[dict[tuple, list[Product]], list[Product]]:
    groups: dict[tuple, list[Product]] = {}
    ungrouped: list[Product] = []

    for product in result.products:
        group_key = _group_key(product)

        if group_key is None:
            ungrouped.append(product)
            continue

        if group_key not in groups:
            groups[group_key] = []

        groups[group_key].append(product)

    return (groups, ungrouped)

def _merge_group(products: list[Product]) -> Product:
    products.sort(key=lambda x: x.marketPrice)
    representative = products[0]

    if len(products) > 1:
        representative.otherSource = [ProductSource(
            source=p.source,
            price=p.price,
            marketPrice=p.marketPrice,
            urlProduct=p.urlProduct
        ) for p in products[1:]]

    return representative

def deduplicate(result: SearchResult) -> SearchResult:
    groups, ungrouped = _group_product(result)

    deduped = [_merge_group(products) for products in groups.values()]
    deduped.extend(ungrouped)

    result.products = deduped
    return result
    