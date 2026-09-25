import json
from pathlib import Path

import pytest

from backend.app.modules.product_search.processors.deduplicator import deduplicate
from backend.app.modules.product_search.processors.normalizer import normalize
from backend.app.modules.product_search.processors.ranker import top_product
from backend.app.modules.product_search.schemas import SearchResult

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "test_product.json"


@pytest.fixture
def raw_result() -> SearchResult:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        products = json.load(f)
    return SearchResult(query="kem chống nắng skin1004", products=products)


def test_pipeline_runs_end_to_end_without_error(raw_result):
    normalize(raw_result)
    deduplicate(raw_result)
    top_product(raw_result, top_k=5)

    assert 0 < len(raw_result.products) <= 5


def test_pipeline_output_has_no_duplicate_urls(raw_result):
    normalize(raw_result)
    deduplicate(raw_result)
    top_product(raw_result, top_k=20)

    urls = [p.urlProduct for p in raw_result.products]
    assert len(urls) == len(set(urls))


def test_pipeline_results_match_query_keyword(raw_result):
    normalize(raw_result)
    deduplicate(raw_result)
    top_product(raw_result, top_k=5)

    assert any("skin1004" in p.name.lower() for p in raw_result.products)
