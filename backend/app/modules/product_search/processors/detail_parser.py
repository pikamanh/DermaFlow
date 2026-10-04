from typing import Optional

_INGREDIENT_MARKER = "thành phần"
_USAGE_MARKER = "hướng dẫn sử dụng"


def split_description_sections(
    text: str,
) -> tuple[str, Optional[list[str]], Optional[str]]:
    """Best-effort split of a free-text product blob into
    (description, ingredients, usage).

    Sites like LamThao/TGSF don't mark these sections with dedicated
    HTML nodes - they're just bold/heading keywords inside one long
    rich-text blob, so this falls back to keyword search instead of
    CSS selectors.
    """
    lower = text.lower()
    ingredient_idx = lower.find(_INGREDIENT_MARKER)
    usage_idx = lower.find(_USAGE_MARKER)

    marker_positions = sorted(
        pos for pos in (ingredient_idx, usage_idx) if pos != -1
    )
    description = (
        text[: marker_positions[0]].strip() if marker_positions else text.strip()
    )

    ingredients = None
    if ingredient_idx != -1:
        end = (
            usage_idx
            if usage_idx != -1 and usage_idx > ingredient_idx
            else len(text)
        )
        chunk = text[ingredient_idx:end]
        chunk = chunk.split(":", 1)[-1] if ":" in chunk[:40] else chunk
        ingredients = [
            item.strip() for item in chunk.split(",") if item.strip()
        ] or None

    usage = None
    if usage_idx != -1:
        end = (
            ingredient_idx
            if ingredient_idx != -1 and ingredient_idx > usage_idx
            else len(text)
        )
        chunk = text[usage_idx:end]
        chunk = chunk.split(":", 1)[-1] if ":" in chunk[:40] else chunk
        usage = chunk.strip() or None

    return description, ingredients, usage
