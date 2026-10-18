# BharatMarkets 🇮🇳📈

> **Educational purposes only. Not SEBI-registered investment advice. Data may be delayed.**

An educational web app for tracking and learning the Indian stock market (NSE/BSE). View live indices, explore stock charts with technical indicators, and understand market trends.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind CSS v4 + shadcn/ui |
| Charts | TradingView Lightweight Charts (candlesticks) + Recharts (analytics) |
| Backend | Python FastAPI (REST + WebSocket) |
| Database | PostgreSQL 16 (SQLAlchemy 2.0 + Alembic) |
| Cache | Redis 7 |
| Data Source | yfinance (delayed ~15min) |
| Deployment | Docker Compose |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### 1. Clone & Configure
```bash
cp .env.example .env
# Edit .env if needed (defaults work for development)
```

### 2. Start with Docker Compose
```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **FastAPI backend** on http://localhost:8000
- **Next.js frontend** on http://localhost:3000

### 3. Seed the Database
```bash
docker-compose exec backend python scripts/seed.py
```

### 4. Open the App
Visit http://localhost:3000

## Local Development (without Docker)

### 1. Environment
```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Add your Gemini key to **`backend/.env`** (required for the AI assistant):
```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash
```
Get a free key from [Google AI Studio](https://aistudio.google.com/apikey). Set `GEMINI_MODEL` to the current Flash model name if Google renames it.

Frontend already defaults `NEXT_PUBLIC_API_URL` to `http://localhost:8000`.

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
# Prophet is optional on Windows — forecast falls back to statsmodels automatically
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend (second terminal)
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — use the floating chat button or visit **/assistant**.

### AI assistant — sample questions
- How is the market today?
- Summarize RELIANCE's last 3 months
- Is TCS trending up or down?
- Compare INFY and TCS
- Should I buy HDFCBANK?

Signals are a transparent point score (SMA, RSI, MACD, 7d forecast). Forecasts show a range plus walk-forward MAPE / directional accuracy. Always educational — not financial advice.

### Tests
```bash
cd backend
venv\Scripts\activate
pytest -q
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/market/status` | Market open/closed status |
| GET | `/api/v1/market/indices` | Live index values |
| GET | `/api/v1/market/gainers` | Top gainers |
| GET | `/api/v1/market/losers` | Top losers |
| GET | `/api/v1/market/sectors` | Sector performance |
| GET | `/api/v1/stocks/search?q=` | Stock search |
| GET | `/api/v1/stocks/{symbol}` | Stock quote |
| GET | `/api/v1/stocks/{symbol}/ohlcv` | OHLCV chart data |
| GET | `/api/v1/stocks/{symbol}/fundamentals` | Fundamentals |
| GET | `/api/v1/stocks/{symbol}/analysis` | Technical analysis + trend |
| POST | `/api/v1/chat` | AI assistant (SSE stream + structured chart data) |
| GET | `/api/v1/chat/health` | Chat / Gemini config check |
| WS | `/ws/prices` | Live price updates |

## Data Sources

- **Market data**: yfinance (Yahoo Finance) — delayed ~15 minutes
- **Stock universe**: NIFTY 50 + NIFTY Next 50 (100 stocks)
- **Holiday calendar**: NSE 2026

## Project Structure

```
BharatMarkets/
├── docker-compose.yml
├── .env.example
├── data/                    # Seed data (stocks, holidays)
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── api/v1/          # Route handlers
│   │   ├── core/            # DB, Redis, market hours
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── providers/       # yfinance + LLM (Gemini)
│   │   ├── schemas/         # Pydantic DTOs
│   │   ├── services/        # Market, history, forecast, signal, chat
│   │   └── utils/           # Symbol resolver (NIFTY 100 names)
│   ├── alembic/             # DB migrations
│   ├── tests/               # pytest
│   └── scripts/             # Seed scripts
└── frontend/                # Next.js 15
    └── src/
        ├── app/             # Pages (dashboard, /assistant, …)
        ├── components/      # UI + chat widget/charts
        ├── lib/             # API client
        ├── hooks/           # React hooks
        ├── providers/       # Context providers
        └── types/           # TypeScript types
```

## AI Chat (Phase 3)

| Piece | Notes |
|-------|--------|
| LLM | Google Gemini via `google-genai` (swappable `LLMProvider` interface) |
| Tools | `get_history`, `get_analysis`, `get_forecast`, `get_signal`, `get_market_overview` |
| Forecast | Prophet if installed; otherwise statsmodels ETS/ARIMA |
| Cache | History 15 min · Forecast 1 hour (Redis when available) |
| Rate limit | 20 chat messages / minute / IP |
| Sentiment | Stub only (`sentiment_service.py`) — FinBERT skipped for now |

## Disclaimer

⚠️ **This application is for educational purposes only.**
- Not registered with SEBI as an investment advisor
- Does not provide investment advice or recommendations
- Market data may be delayed by 15+ minutes
- No real money or real orders are involved
