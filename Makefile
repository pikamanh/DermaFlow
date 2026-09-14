PY := uv run python -m
PORT_BACKEND := 8001

test hasaki:
	$(PY) backend.app.modules.product_search.providers.hasaki

run backend:
	uvicorn backend.app.main:app --reload --port $(PORT_BACKEND)