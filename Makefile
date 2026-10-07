UV := uv run
PY := python -m
PORT_BACKEND := 8001

hasaki:
	$(UV) $(PY) backend.app.modules.product_search.providers.hasaki

lamthao:
	$(UV) $(PY) backend.app.modules.product_search.providers.lamthao

tgsf:
	$(UV) $(PY) backend.app.modules.product_search.providers.tgsf

services:
	$(UV) $(PY) backend.app.modules.product_search.services

normalize:
	$(UV) $(PY) backend.app.modules.product_search.processors.normalizer

fallback:
	$(UV) $(PY) backend.tests.product_search.test_google_fallback

cache:
	$(UV) $(PY) backend.tests.product_search.test_cache_manual

run-backend:
	uvicorn backend.app.main:app --reload --port $(PORT_BACKEND)

pytest:
	$(UV) pytest -s -v