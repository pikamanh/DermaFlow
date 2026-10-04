from typing import Optional

from pydantic import BaseModel

class ProductSource(BaseModel):
    source: str
    price: int
    marketPrice: int
    urlProduct: str

class Product(BaseModel):
    name: str
    brandName: Optional[str] = None
    volume: Optional[str] = None
    marketPrice: int
    price: int
    discountPercent: Optional[float] = None
    categoryName: Optional[str] = None
    urlProduct: str
    source: str
    otherSource: Optional[list[ProductSource]] = None

class ProductDetail(BaseModel):
    name: str
    brandName: Optional[str] = None
    volume: Optional[str] = None
    marketPrice: Optional[int] = None
    price: int
    ingredients: Optional[list[str]] = None
    description: Optional[str] = None
    usage: Optional[str] = None
    urlProduct: str
    source: str

class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    query: str
    products: Optional[list[Product]] = None

def parse_product(data: dict, source: str) -> Product:
    brand = data.get("brand") or {}
    price = data["price"]

    return Product(
        name=data["name"],
        brandName=brand.get("name"),
        marketPrice=data.get("market_price") or price,
        price=price,
        discountPercent=data.get("discount_percent"),
        categoryName=data.get("category_name_level"),
        urlProduct=data["product_url"],
        source=source,
    )