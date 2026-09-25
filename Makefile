PY := uv run python -m
PORT_BACKEND := 8001

hasaki:
	$(PY) backend.app.modules.product_search.providers.hasaki

lamthao:
	$(PY) backend.app.modules.product_search.providers.lamthao

tgsf:
	$(PY) backend.app.modules.product_search.providers.tgsf

services:
	$(PY) backend.app.modules.product_search.services

normalize:
	$(PY) backend.app.modules.product_search.processors.normalizer

fallback:
	$(PY) backend.tests.product_search.test_google_fallback

run backend:
	uvicorn backend.app.main:app --reload --port $(PORT_BACKEND)