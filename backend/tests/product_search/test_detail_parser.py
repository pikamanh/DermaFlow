from backend.app.modules.product_search.processors.detail_parser import (
    split_description_sections,
)


def test_split_with_both_markers():
    text = (
        "Kem chống nắng dịu nhẹ cho da nhạy cảm.\n"
        "Thành phần: Water, Niacinamide, Glycerin\n"
        "Hướng dẫn sử dụng: Thoa đều lên da trước khi ra ngoài."
    )

    description, ingredients, usage = split_description_sections(text)

    assert description == "Kem chống nắng dịu nhẹ cho da nhạy cảm."
    assert ingredients == ["Water", "Niacinamide", "Glycerin"]
    assert usage == "Thoa đều lên da trước khi ra ngoài."


def test_split_with_usage_before_ingredients():
    text = (
        "Mô tả sản phẩm ngắn.\n"
        "Hướng dẫn sử dụng: Thoa buổi sáng.\n"
        "Thành phần: Aqua, Titanium Dioxide"
    )

    description, ingredients, usage = split_description_sections(text)

    assert description == "Mô tả sản phẩm ngắn."
    assert usage == "Thoa buổi sáng."
    assert ingredients == ["Aqua", "Titanium Dioxide"]


def test_split_with_only_ingredients_marker():
    text = "Mô tả sản phẩm.\nThành phần: Aqua, Alcohol"

    description, ingredients, usage = split_description_sections(text)

    assert description == "Mô tả sản phẩm."
    assert ingredients == ["Aqua", "Alcohol"]
    assert usage is None


def test_split_with_only_usage_marker():
    text = "Mô tả sản phẩm.\nHướng dẫn sử dụng: Thoa đều lên da."

    description, ingredients, usage = split_description_sections(text)

    assert description == "Mô tả sản phẩm."
    assert ingredients is None
    assert usage == "Thoa đều lên da."


def test_split_with_no_markers_returns_full_text_as_description():
    text = "Sản phẩm chống nắng dịu nhẹ, phù hợp cho mọi loại da."

    description, ingredients, usage = split_description_sections(text)

    assert description == text
    assert ingredients is None
    assert usage is None


def test_split_ingredients_without_colon_falls_back_to_whole_chunk():
    text = "Mô tả.\nThành phần nổi bật gồm Niacinamide và Centella."

    _, ingredients, _ = split_description_sections(text)

    assert ingredients == ["Thành phần nổi bật gồm Niacinamide và Centella."]
