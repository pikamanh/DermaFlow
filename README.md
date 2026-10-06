# DermaFlow

> Trợ lý làm đẹp thông minh: tìm kiếm mỹ phẩm theo thời gian thực từ nhiều website, chatbot tư vấn có tool calling, phân tích da qua ảnh khuôn mặt và gợi ý sản phẩm cá nhân hóa.

DermaFlow là backend **FastAPI** được xây theo kiến trúc **Modular Monolith**: mỗi chức năng (product search, chat, vision, recommendation) là một module độc lập trong `backend/app/modules/`, tầng `api/` chỉ nhận/trả HTTP và gọi service.

---

## Mục lục

- [Features](#features)
- [Kiến trúc & Flow hoạt động](#kiến-trúc--flow-hoạt-động)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Cài đặt & Chạy](#cài-đặt--chạy)
- [API](#api)
- [Tiến trình phát triển](#tiến-trình-phát-triển)

---

## Features

### ✅ Đã hoàn thành

- **Real-time Product Search** từ 3 website mỹ phẩm Việt Nam:
  - [Hasaki](https://hasaki.vn)
  - [Lâm Thảo Cosmetics](https://lamthaocosmetics.vn)
  - [Thế Giới Skinfood](https://thegioiskinfood.com)
- **Tìm kiếm song song** (`asyncio.gather`) — một provider lỗi không làm hỏng toàn bộ request; có log latency từng provider.
- **Xử lý kết quả**:
  - *Normalize* — chuẩn hóa tên, giá, dung tích.
  - *Deduplicate* — gộp sản phẩm trùng theo `name + brand + volume`, giữ nơi bán rẻ nhất và liệt kê các nguồn khác trong `otherSource` (tiện so sánh giá).
  - *Rank* — xếp hạng theo độ liên quan với query, đảm bảo mỗi nguồn đều có đại diện trong top-K.
- **Cache in-memory có TTL** cho cả kết quả search và product detail — query lặp lại trả về ngay lập tức.
- **Product Detail** — lấy thành phần (ingredients), mô tả, hướng dẫn sử dụng từ URL sản phẩm; tự định tuyến tới đúng provider theo domain.

### 🚧 Đang phát triển

- **Beauty Chatbot** dùng LLM qua API tương thích OpenAI.
- **Google Fallback** khi kết quả từ 3 nguồn quá ít (đã có khung code, chưa sử dụng được).

### 🗓️ Kế hoạch

- **Tool Calling** — chatbot tự gọi `search_products` / `get_product_detail`.
- **RAG** — trả lời kiến thức làm đẹp chung từ knowledge base.
- **Facial / Skin Analysis** — kiểm tra chất lượng ảnh, phát hiện khuôn mặt, chia vùng (trán, má, mũi, cằm), phân tích đặc điểm da (mụn, dầu, sắc tố).
- **Skin Profile** — chuẩn hóa kết quả vision thành hồ sơ da (không phải chẩn đoán y khoa).
- **Personalized Recommendation** — gợi ý sản phẩm/routine theo hồ sơ da, ngân sách và nhu cầu, kèm lý do.

---

## Kiến trúc & Flow hoạt động

### Nguyên tắc

- `api/` chỉ xử lý HTTP; business logic nằm trong `modules/`.
- Mỗi website là một `provider` riêng, cùng implement interface `ProductSearchProvider` và trả về chung schema `Product`.
- Chatbot gọi tool → tool gọi service; **LLM không tự crawl website**.
- Vision độc lập với chatbot, giao tiếp qua `SkinProfile`.

### Flow Product Search (hiện tại)

```text
GET /products/search?query=...
            │
            ▼
   ProductSearchService
            │
     ┌── Cache HIT? ──── Yes ──► Trả kết quả
     │       │
     │       No
     │       ▼
     │  ┌──────────┬──────────────┬──────────────────┐
     │  ▼          ▼              ▼                  │  (song song)
     │ Hasaki   LamThao   TheGioiSkinfood            │
     │  └──────────┴──────┬───────┘                  │
     │                    ▼
     │               Raw Results
     │                    ▼
     │   Normalize → Deduplicate → Rank (Top K)
     │                    ▼
     │        Đủ kết quả? ── No ──► Google Fallback (WIP)
     │                    │
     │                   Yes
     │                    ▼
     └────────────── Lưu cache ──► SearchResult
```

### Flow Product Detail

```text
GET /products/detail?url=...
        │
        ▼
Xác định provider theo domain (hasaki.vn / lamthaocosmetics.vn / thegioiskinfood.com)
        │
        ▼
Detail cache HIT? ── Yes ──► Trả kết quả
        │ No
        ▼
Provider.get_detail(url) → ProductDetail (ingredients, description, usage, ...)
```

### Flow MVP mục tiêu

```text
Upload ảnh khuôn mặt
        ▼
Vision: Validation → Face Detection → Regions → Skin Features
        ▼
SkinProfile
        ▼
User: "Routine dưới 1 triệu cho da dầu mụn"
        ▼
Chatbot ──► Recommendation Rules ──► Product Search ──► Ranking
        ▼
Câu trả lời: routine + sản phẩm + giá + nguồn + lý do
```

---

## Cấu trúc thư mục

```text
DermaFlow/
├── backend/
│   ├── app/
│   │   ├── main.py                    # Entry point FastAPI
│   │   ├── api/
│   │   │   ├── router.py              # Router gốc + /health
│   │   │   └── v1/products.py         # /products/search, /products/detail
│   │   ├── core/
│   │   │   ├── config.py              # Đọc biến môi trường
│   │   │   └── logging.py
│   │   └── modules/
│   │       ├── cache.py               # TTLCache in-memory
│   │       ├── chat/                  # Chatbot (WIP)
│   │       └── product_search/
│   │           ├── schemas.py         # Product, ProductDetail, SearchQuery, SearchResult
│   │           ├── services.py        # ProductSearchService (điều phối)
│   │           ├── providers/         # base, hasaki, lamthao, tgsf
│   │           ├── processors/        # normalizer, deduplicator, ranker, detail_parser
│   │           └── fallback/google.py
│   └── tests/
├── plan.md                            # Roadmap chi tiết theo phase
├── Makefile
└── pyproject.toml
```

---

## Cài đặt & Chạy

### Yêu cầu

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/)

### Cài đặt

```bash
git clone <repo-url> DermaFlow
cd DermaFlow
uv sync
```

### Biến môi trường

Tạo file `.env` ở thư mục gốc:

```env
# Product search
FALLBACK_MIN_RESULTS=3
CACHE_TTL_SECONDS=300

# Google fallback (chưa bắt buộc)
GOOGLE_API_KEY=
GOOGLE_CSE_ID=

# Chatbot – API tương thích OpenAI
BASE_URL=
API_KEY=
MODEL=
```

### Chạy backend

```bash
make run-backend          # uvicorn tại http://localhost:8001
```

- Swagger UI: http://localhost:8001/docs
- Health check: http://localhost:8001/health

### Test

```bash
uv run pytest             # Chạy toàn bộ test trong backend/tests

# Chạy thử từng thành phần
make hasaki               # Provider Hasaki
make lamthao              # Provider Lâm Thảo
make tgsf                 # Provider Thế Giới Skinfood
make services             # Pipeline search đầy đủ
make cache                # Kiểm tra cache HIT/MISS
```

---

## API

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/health` | Kiểm tra trạng thái server |
| `GET` | `/products/search?query=<từ khóa>` | Tìm sản phẩm từ 3 nguồn, đã normalize/dedupe/rank |
| `GET` | `/products/detail?url=<url sản phẩm>` | Lấy chi tiết sản phẩm (ingredients, description, usage) |
| `GET` | `/products/chat?query=<câu hỏi>` | Chatbot cơ bản *(đang phát triển)* |

Ví dụ response `/products/search?query=kem chống nắng`:

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

## Tiến trình phát triển

Chi tiết checklist từng phase xem tại [`plan.md`](plan.md).

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0 | Setup Foundation (FastAPI, `/health`, config, logging) | ✅ Hoàn thành |
| 1 | Product Schema + Provider Interface | ✅ Hoàn thành |
| 2 | Provider Hasaki | ✅ Hoàn thành |
| 3 | Product Search Service + API | ✅ Hoàn thành |
| 4 | Provider Lâm Thảo + Thế Giới Skinfood + Parallel Search | ✅ Hoàn thành |
| 5 | Normalize + Deduplicate + Rank | ✅ Hoàn thành |
| 6 | Cache + Google Fallback | 🟡 Cache xong, Google fallback chưa dùng được |
| 7 | Product Detail | ✅ Hoàn thành |
| 8 | Basic Chatbot | 🚧 Đang thực hiện |
| 9 | Tool Calling | ⏳ Chưa bắt đầu |
| 10 | Beauty Knowledge + RAG | ⏳ Chưa bắt đầu |
| 11 | Vision Foundation | ⏳ Chưa bắt đầu |
| 12 | Facial Regions | ⏳ Chưa bắt đầu |
| 13 | Skin Feature Analysis | ⏳ Chưa bắt đầu |
| 14 | Skin Profile | ⏳ Chưa bắt đầu |
| 15 | Rule-Based Recommendation | ⏳ Chưa bắt đầu |
| 16 | Integration: Face + Chatbot + Recommendation (MVP) | ⏳ Chưa bắt đầu |
| 17 | Evaluation | ⏳ Chưa bắt đầu |
| 18 | Deployment | ⏳ Chưa bắt đầu |

**Milestone hiện tại:** M4 (Search 3 nguồn + Normalize + Rank + Cache) ✅ → đang hướng tới **M5 – Basic Chatbot**.

---

## Lưu ý

- DermaFlow **không** đưa ra chẩn đoán y khoa. Kết quả phân tích da (khi hoàn thành) chỉ mang tính tham khảo về đặc điểm nhìn thấy được.
- Dữ liệu sản phẩm được lấy từ các website công khai; giá và tình trạng hàng có thể thay đổi theo thời gian.
