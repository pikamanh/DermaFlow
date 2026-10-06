# DermaFlow

> A smart beauty assistant: real-time cosmetics search across multiple websites, a tool-calling beauty chatbot, facial skin analysis, and personalized product recommendations.

DermaFlow is a **FastAPI** backend built as a **Modular Monolith**. Each capability (product search, chat, vision, recommendation) is an independent module under `backend/app/modules/`. The `api/` layer only handles HTTP and delegates to services.

---

## Table of Contents

- [Features](#features)
- [Architecture & Flow](#architecture--flow)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API](#api)
- [Progress](#progress)

---

## Features

### ✅ Completed

- **Real-time Product Search** across 3 Vietnamese cosmetics retailers:
  - [Hasaki](https://hasaki.vn)
  - [Lam Thao Cosmetics](https://lamthaocosmetics.vn)
  - [The Gioi Skinfood](https://thegioiskinfood.com)
- **Parallel search** (`asyncio.gather`): one failing provider doesn't break the whole request, and each provider's latency is logged.
- **Result processing**:
  - *Normalize*: standardizes names, prices and volumes.
  - *Deduplicate*: merges duplicate products by `name + brand + volume`. It keeps the cheapest offer and lists the other retailers in `otherSource`, so prices can be compared.
  - *Rank*: orders results by query relevance and makes sure every source is represented in the top-K.
- **In-memory TTL cache** for both search results and product details, so repeated queries return instantly.
- **Product Detail**: fetches ingredients, description and usage instructions from a product URL. The request is routed to the right provider based on the URL's domain.

### 🚧 In Progress

- **Beauty Chatbot** backed by an LLM through an OpenAI-compatible API.
- **Google Fallback** for when the 3 sources return too few results. The code skeleton exists but it is not working yet.

### 🗓️ Planned

- **Tool Calling**: the chatbot calls `search_products` / `get_product_detail` on its own.
- **RAG**: answers general beauty questions from a knowledge base.
- **Facial / Skin Analysis**: image quality checks, face detection, facial regions (forehead, cheeks, nose, chin), and skin feature analysis (acne, oiliness, pigmentation).
- **Skin Profile**: turns vision output into a standardized skin profile. This is not a medical diagnosis.
- **Personalized Recommendation**: suggests products and routines based on skin profile, budget and needs, and explains each suggestion.

---

## Architecture & Flow

### Principles

- `api/` only handles HTTP; business logic lives in `modules/`.
- Each website is its own `provider`. Every provider implements the `ProductSearchProvider` interface and returns the shared `Product` schema.
- The chatbot calls tools and tools call services. **The LLM never crawls websites directly.**
- Vision is independent of the chatbot; they communicate through `SkinProfile`.

### Product Search Flow (current)

```text
GET /products/search?query=...
            │
            ▼
   ProductSearchService
            │
     ┌── Cache HIT? ──── Yes ──► Return result
     │       │
     │       No
     │       ▼
     │  ┌──────────┬──────────────┬──────────────────┐
     │  ▼          ▼              ▼                  │  (parallel)
     │ Hasaki   LamThao   TheGioiSkinfood            │
     │  └──────────┴──────┬───────┘                  │
     │                    ▼
     │               Raw Results
     │                    ▼
     │   Normalize → Deduplicate → Rank (Top K)
     │                    ▼
     │        Enough results? ── No ──► Google Fallback (WIP)
     │                    │
     │                   Yes
     │                    ▼
     └────────────── Store in cache ──► SearchResult
```

### Product Detail Flow

```text
GET /products/detail?url=...
        │
        ▼
Resolve provider by domain (hasaki.vn / lamthaocosmetics.vn / thegioiskinfood.com)
        │
        ▼
Detail cache HIT? ── Yes ──► Return result
        │ No
        ▼
Provider.get_detail(url) → ProductDetail (ingredients, description, usage, ...)
```

### Target MVP Flow

```text
Upload face photo
        ▼
Vision: Validation → Face Detection → Regions → Skin Features
        ▼
SkinProfile
        ▼
User: "A routine under 1 million VND for oily, acne-prone skin"
        ▼
Chatbot ──► Recommendation Rules ──► Product Search ──► Ranking
        ▼
Response: routine + products + prices + sources + reasons
```

---

## Project Structure

```text
DermaFlow/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── api/
│   │   │   ├── router.py              # Root router + /health
│   │   │   └── v1/products.py         # /products/search, /products/detail
│   │   ├── core/
│   │   │   ├── config.py              # Environment settings
│   │   │   └── logging.py
│   │   └── modules/
│   │       ├── cache.py               # In-memory TTLCache
│   │       ├── chat/                  # Chatbot (WIP)
│   │       └── product_search/
│   │           ├── schemas.py         # Product, ProductDetail, SearchQuery, SearchResult
│   │           ├── services.py        # ProductSearchService (orchestration)
│   │           ├── providers/         # base, hasaki, lamthao, tgsf
│   │           ├── processors/        # normalizer, deduplicator, ranker, detail_parser
│   │           └── fallback/google.py
│   └── tests/
├── plan.md                            # Detailed phase-by-phase roadmap
├── Makefile
└── pyproject.toml
```

---

## Getting Started

### Requirements

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/)

### Installation

```bash
git clone <repo-url> DermaFlow
cd DermaFlow
uv sync
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Product search
FALLBACK_MIN_RESULTS=3
CACHE_TTL_SECONDS=300

# Google fallback (optional for now)
GOOGLE_API_KEY=
GOOGLE_CSE_ID=

# Chatbot – OpenAI-compatible API
BASE_URL=
API_KEY=
MODEL=
```

### Run the Backend

```bash
make run-backend          # uvicorn at http://localhost:8001
```

- Swagger UI: http://localhost:8001/docs
- Health check: http://localhost:8001/health

### Testing

```bash
uv run pytest             # Run all tests in backend/tests

# Try individual components
make hasaki               # Hasaki provider
make lamthao              # Lam Thao provider
make tgsf                 # The Gioi Skinfood provider
make services             # Full search pipeline
make cache                # Cache HIT/MISS check
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server health check |
| `GET` | `/products/search?query=<keyword>` | Search products across 3 sources (normalized, deduplicated and ranked) |
| `GET` | `/products/detail?url=<product url>` | Get product details (ingredients, description, usage) |
| `GET` | `/products/chat?query=<question>` | Basic chatbot *(in progress)* |

Example response for `/products/search?query=kem chống nắng` (sunscreen):

```json
{
  "query": "kem chống nắng",
  "products": [
    {
      "name": "...",
      "brandName": "...",
      "volume": "50ml",
      "marketPrice": 450000,
      "price": 389000,
      "discountPercent": 13.6,
      "urlProduct": "https://hasaki.vn/...",
      "source": "hasaki",
      "otherSource": [
        { "source": "tgsf", "price": 399000, "marketPrice": 450000, "urlProduct": "https://thegioiskinfood.com/..." }
      ]
    }
  ]
}
```

---

## Progress

See [`plan.md`](plan.md) for the detailed checklist of each phase.

| Phase | Scope | Status |
|---|---|---|
| 0 | Setup Foundation (FastAPI, `/health`, config, logging) | ✅ Done |
| 1 | Product Schema + Provider Interface | ✅ Done |
| 2 | Hasaki Provider | ✅ Done |
| 3 | Product Search Service + API | ✅ Done |
| 4 | Lam Thao + The Gioi Skinfood Providers + Parallel Search | ✅ Done |
| 5 | Normalize + Deduplicate + Rank | ✅ Done |
| 6 | Cache + Google Fallback | 🟡 Cache done, Google fallback not working yet |
| 7 | Product Detail | ✅ Done |
| 8 | Basic Chatbot | 🚧 In progress |
| 9 | Tool Calling | ⏳ Not started |
| 10 | Beauty Knowledge + RAG | ⏳ Not started |
| 11 | Vision Foundation | ⏳ Not started |
| 12 | Facial Regions | ⏳ Not started |
| 13 | Skin Feature Analysis | ⏳ Not started |
| 14 | Skin Profile | ⏳ Not started |
| 15 | Rule-Based Recommendation | ⏳ Not started |
| 16 | Integration: Face + Chatbot + Recommendation (MVP) | ⏳ Not started |
| 17 | Evaluation | ⏳ Not started |
| 18 | Deployment | ⏳ Not started |

**Current milestone:** M4 (3-source search + Normalize + Rank + Cache) ✅ → working towards **M5 – Basic Chatbot**.

---

## Disclaimer

- DermaFlow does **not** provide medical diagnoses. Skin analysis results, once available, describe visible features only and are for reference.
- Product data is collected from public websites. Prices and availability may change over time.
