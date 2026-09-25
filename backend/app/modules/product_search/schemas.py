from typing import Optional

from pydantic import BaseModel

class ProductSource(BaseModel):
    source: str
    price: int
    marketPrice: int
    urlProduct: str

class Product(BaseModel):
    name: str
    englishName: Optional[str] = None
    brandName: Optional[str] = None
    volume: Optional[str] = None
    marketPrice: int
    price: int
    discountPercent: Optional[float] = None
    quantity: Optional[int] = None
    boughtCount: Optional[int] = None
    dealID: Optional[int] = None
    dealQuantity: Optional[int] = None
    dealBoughtPercent: Optional[int] = None
    dealStart: Optional[int] = None
    dealEnd: Optional[int] = None
    dealTimeRemain: Optional[int] = None
    categoryName: Optional[str] = None
    categoryID: Optional[int] = None
    urlProduct: str
    source: str
    otherSource: Optional[list[ProductSource]] = None

class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    query: str
    products: Optional[list[Product]] = None

def parse_product(data: dict, source: str) -> Product:
    deal = data.get("deal") or {}
    brand = data.get("brand") or {}

    return Product(
        name=data["name"],
        englishName=data.get("english_name"),
        brandName=brand.get("name"),
        marketPrice=data["market_price"],
        price=data["price"],
        discountPercent=data.get("discount_percent"),
        quantity=data.get("quantity"),
        boughtCount=data.get("bought_count"),

        dealID=deal.get("deal_id"),
        dealQuantity=deal.get("quantity"),
        dealBoughtPercent=deal.get("bought_percent"),
        dealStart=deal.get("start"),
        dealEnd=deal.get("expired"),
        dealTimeRemain=deal.get("time_remain"),

        categoryName=data.get("category_name_level"),
        categoryID=data.get("category_id"),

        urlProduct=data["product_url"],
        source=source,
    )