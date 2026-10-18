"""Market data service — works with or without database/Redis."""

import json
from datetime import datetime, timezone
from decimal import Decimal
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core import market_hours
from app.core.redis_client import cache_get, cache_set
from app.providers.base import MarketDataProvider
from app.schemas.market import (
    IndexResponse,
    MarketBreadthResponse,
    MarketStatusResponse,
    SectorPerformanceResponse,
    StockQuoteResponse,
)

logger = logging.getLogger(__name__)

TRACKED_INDICES = [
    {"symbol": "^NSEI", "display_name": "NIFTY 50", "exchange": "NSE"},
    {"symbol": "^BSESN", "display_name": "SENSEX", "exchange": "BSE"},
    {"symbol": "^NSEBANK", "display_name": "BANK NIFTY", "exchange": "NSE"},
    {"symbol": "^CNXIT", "display_name": "NIFTY IT", "exchange": "NSE"},
]


def _load_stock_list() -> List[Dict[str, Any]]:
    """Load NIFTY 100 stock list from data file."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty_100_stocks.json",
        Path(__file__).resolve().parent.parent.parent / "data" / "nifty_100_stocks.json",
        Path.cwd() / "data" / "nifty_100_stocks.json",
        Path.cwd().parent / "data" / "nifty_100_stocks.json",
    ]
    for p in candidates:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("stocks", data) if isinstance(data, dict) else data
    return []


class MarketService:
    """Coordinates market data — gracefully handles missing DB/Redis."""

    def __init__(
        self,
        db: Any = None,
        redis: Any = None,
        provider: Optional[MarketDataProvider] = None,
    ):
        self.db = db
        self.redis = redis
        self.provider = provider
        self._all_quotes_cache: Optional[List[Dict[str, Any]]] = None

    def get_market_status(self) -> MarketStatusResponse:
        """Fetch current trading status and session timings."""
        status_dict = market_hours.get_market_status()
        return MarketStatusResponse(**status_dict)

    async def _get_all_quotes(self) -> List[Dict[str, Any]]:
        """Fetch quotes for all NIFTY 100 stocks with caching."""
        # In-memory cache (within same request lifecycle)
        if self._all_quotes_cache is not None:
            return self._all_quotes_cache

        # Try Redis cache first
        cache_key = "market:all_quotes"
        cached = await cache_get(cache_key)
        if cached:
            self._all_quotes_cache = cached
            return cached

        if not self.provider:
            return []

        # Load stock list from JSON file
        stock_list = _load_stock_list()
        if not stock_list:
            logger.warning("Could not load stock list from data files")
            return []

        symbols = [s.get("symbol", s.get("ticker", "")) for s in stock_list if s.get("symbol") or s.get("ticker")]
        # Build a lookup for name/sector
        meta = {}
        for s in stock_list:
            sym = s.get("symbol", s.get("ticker", ""))
            meta[sym] = {"name": s.get("name", s.get("company", sym)), "sector": s.get("sector", "")}

        logger.info("Fetching bulk quotes for %d stocks via yfinance...", len(symbols))
        quotes = await self.provider.get_bulk_quotes(symbols)

        # Enrich with name/sector from the JSON metadata
        enriched = []
        for q in quotes:
            sym = q.get("symbol", "")
            m = meta.get(sym, {})
            q["name"] = m.get("name", sym)
            q["sector"] = m.get("sector", "")
            enriched.append(q)

        # Cache for 5 minutes
        await cache_set(cache_key, enriched, ttl=300)
        self._all_quotes_cache = enriched
        return enriched

    async def get_indices(self) -> List[IndexResponse]:
        """Fetch quotes for benchmark indices."""
        cache_key = "market:indices"
        cached = await cache_get(cache_key)
        if cached:
            return [IndexResponse(**item) for item in cached]

        results: List[IndexResponse] = []
        if self.provider:
            for item in TRACKED_INDICES:
                try:
                    data = await self.provider.get_index_data(
                        item["symbol"], display_name=item["display_name"]
                    )
                    # Also fetch day_high/day_low from quote
                    quote = await self.provider.get_quote(item["symbol"])
                    results.append(
                        IndexResponse(
                            symbol=item["symbol"],
                            display_name=item["display_name"],
                            ltp=data["ltp"],
                            change=data["change"],
                            change_pct=data["change_pct"],
                            exchange=item["exchange"],
                            day_high=quote.get("day_high"),
                            day_low=quote.get("day_low"),
                        )
                    )
                except Exception as e:
                    logger.warning("Failed to fetch index %s: %s", item["symbol"], e)

        if results:
            await cache_set(cache_key, [r.model_dump() for r in results])

        return results

    async def get_top_gainers(self, limit: int = 10) -> List[StockQuoteResponse]:
        """Fetch top market gainers sorted by % change descending."""
        cache_key = f"market:gainers:{limit}"
        cached = await cache_get(cache_key)
        if cached:
            return [StockQuoteResponse(**item) for item in cached]

        quotes = await self._get_all_quotes()
        # Filter positive change, sort descending
        positive = [q for q in quotes if q.get("change_pct") and float(q["change_pct"]) > 0]
        positive.sort(key=lambda q: float(q.get("change_pct", 0)), reverse=True)
        top = positive[:limit]

        results = self._quotes_to_response(top)
        if results:
            await cache_set(cache_key, [r.model_dump() for r in results])
        return results

    async def get_top_losers(self, limit: int = 10) -> List[StockQuoteResponse]:
        """Fetch top market losers sorted by % change ascending."""
        cache_key = f"market:losers:{limit}"
        cached = await cache_get(cache_key)
        if cached:
            return [StockQuoteResponse(**item) for item in cached]

        quotes = await self._get_all_quotes()
        negative = [q for q in quotes if q.get("change_pct") and float(q["change_pct"]) < 0]
        negative.sort(key=lambda q: float(q.get("change_pct", 0)))
        top = negative[:limit]

        results = self._quotes_to_response(top)
        if results:
            await cache_set(cache_key, [r.model_dump() for r in results])
        return results

    async def get_sector_performance(self, period: str = "1d") -> List[SectorPerformanceResponse]:
        """Compute sector-level aggregate performance."""
        cache_key = f"market:sectors:{period}"
        cached = await cache_get(cache_key)
        if cached:
            return [SectorPerformanceResponse(**item) for item in cached]

        quotes = await self._get_all_quotes()
        # Group by sector
        sectors: Dict[str, List[float]] = {}
        for q in quotes:
            sector = q.get("sector", "").strip()
            if not sector:
                continue
            pct = float(q.get("change_pct", 0))
            sectors.setdefault(sector, []).append(pct)

        results: List[SectorPerformanceResponse] = []
        for sector_name, pcts in sectors.items():
            avg_change = sum(pcts) / len(pcts) if pcts else 0
            results.append(
                SectorPerformanceResponse(
                    sector=sector_name,
                    change_pct=Decimal(str(round(avg_change, 4))),
                    stock_count=len(pcts),
                )
            )

        results.sort(key=lambda s: float(s.change_pct), reverse=True)

        if results:
            await cache_set(cache_key, [s.model_dump() for s in results])
        return results

    async def get_market_breadth(self) -> MarketBreadthResponse:
        """Count advances vs declines from all quotes."""
        cache_key = "market:breadth"
        cached = await cache_get(cache_key)
        if cached:
            return MarketBreadthResponse(**cached)

        quotes = await self._get_all_quotes()
        advances = sum(1 for q in quotes if float(q.get("change_pct", 0)) > 0)
        declines = sum(1 for q in quotes if float(q.get("change_pct", 0)) < 0)
        unchanged = sum(1 for q in quotes if float(q.get("change_pct", 0)) == 0)
        total = len(quotes)

        ratio = Decimal(str(round(advances / declines, 4))) if declines > 0 else None

        result = MarketBreadthResponse(
            advances=advances,
            declines=declines,
            unchanged=unchanged,
            total=total,
            advance_decline_ratio=ratio,
        )

        await cache_set(cache_key, result.model_dump())
        return result

    def _quotes_to_response(self, quotes: List[Dict[str, Any]]) -> List[StockQuoteResponse]:
        """Convert raw quote dicts to StockQuoteResponse objects."""
        results = []
        now_utc = datetime.now(timezone.utc)
        for q in quotes:
            try:
                results.append(
                    StockQuoteResponse(
                        symbol=q.get("symbol", ""),
                        name=q.get("name", q.get("symbol", "")),
                        sector=q.get("sector"),
                        ltp=Decimal(str(q.get("ltp", 0))),
                        prev_close=Decimal(str(q.get("prev_close", 0))),
                        change=Decimal(str(q.get("change", 0))),
                        change_pct=Decimal(str(q.get("change_pct", 0))),
                        day_high=Decimal(str(q["day_high"])) if q.get("day_high") else None,
                        day_low=Decimal(str(q["day_low"])) if q.get("day_low") else None,
                        high_52w=Decimal(str(q["high_52w"])) if q.get("high_52w") else None,
                        low_52w=Decimal(str(q["low_52w"])) if q.get("low_52w") else None,
                        volume=q.get("volume"),
                        exchange=q.get("exchange", "NSE"),
                        updated_at=q.get("updated_at", now_utc),
                    )
                )
            except Exception as e:
                logger.debug("Skipping quote %s: %s", q.get("symbol"), e)
        return results
