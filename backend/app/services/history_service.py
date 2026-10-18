"""Historical daily price summaries for chat and charts."""

from __future__ import annotations

from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

from app.core.redis_client import cache_get, cache_set
from app.providers.base import MarketDataProvider
from app.schemas.chat import HistorySummary, PricePoint
from app.utils.symbol_resolver import load_stock_universe, resolve_symbol

logger = logging.getLogger(__name__)

PERIOD_TO_YF: Dict[str, str] = {
    "1W": "5d",
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
}

CACHE_TTL_SECONDS = 15 * 60  # 15 minutes


def _company_name(symbol: str) -> Optional[str]:
    for s in load_stock_universe():
        sym = (s.get("symbol") or s.get("ticker") or "").upper()
        if sym == symbol.upper():
            return s.get("name") or s.get("company")
    return None


def _downsample_series(points: List[PricePoint], max_points: int = 90) -> List[PricePoint]:
    """Keep chart payloads light while preserving endpoints."""
    if len(points) <= max_points:
        return points
    step = max(1, len(points) // max_points)
    sampled = points[::step]
    if sampled[-1].date != points[-1].date:
        sampled.append(points[-1])
    return sampled


class HistoryService:
    """Fetch and summarize past daily prices via the market data provider."""

    def __init__(self, provider: MarketDataProvider):
        self.provider = provider

    async def get_history(
        self,
        symbol_or_name: str,
        period: str = "3M",
    ) -> HistorySummary:
        """
        Return start/end/% change/high/low plus a short series for charts.

        Args:
            symbol_or_name: NSE ticker or company name (e.g. RELIANCE, Reliance).
            period: One of 1W, 1M, 3M, 6M, 1Y.
        """
        period_key = period.strip().upper()
        if period_key not in PERIOD_TO_YF:
            raise ValueError(f"Unsupported period '{period}'. Use one of: {', '.join(PERIOD_TO_YF)}")

        resolved = resolve_symbol(symbol_or_name)
        if not resolved:
            raise ValueError(f"Could not resolve stock symbol from '{symbol_or_name}'.")

        cache_key = f"history:{resolved}:{period_key}"
        cached = await cache_get(cache_key)
        if cached:
            return HistorySummary(**cached)

        yf_period = PERIOD_TO_YF[period_key]
        bars = await self.provider.get_ohlcv(symbol=resolved, interval="1d", period=yf_period)
        if not bars or len(bars) < 2:
            raise ValueError(f"Insufficient history for {resolved} ({period_key}).")

        closes = [Decimal(str(b["close"])) for b in bars]
        highs = [Decimal(str(b["high"])) for b in bars]
        lows = [Decimal(str(b["low"])) for b in bars]
        start_price = closes[0]
        end_price = closes[-1]
        change_pct = (
            ((end_price - start_price) / start_price) * Decimal("100")
            if start_price != 0
            else Decimal("0")
        )

        series = [
            PricePoint(date=str(b["date"]), close=Decimal(str(b["close"])))
            for b in bars
            if b.get("date") is not None and b.get("close") is not None
        ]

        summary = HistorySummary(
            symbol=resolved,
            name=_company_name(resolved),
            period=period_key,
            start_price=start_price.quantize(Decimal("0.0001")),
            end_price=end_price.quantize(Decimal("0.0001")),
            change_pct=change_pct.quantize(Decimal("0.0001")),
            high=max(highs).quantize(Decimal("0.0001")),
            low=min(lows).quantize(Decimal("0.0001")),
            series=_downsample_series(series),
        )

        await cache_set(cache_key, summary.model_dump(mode="json"), ttl=CACHE_TTL_SECONDS)
        return summary

    async def get_ohlcv_closes(
        self,
        symbol: str,
        period: str = "2y",
    ) -> List[Dict[str, Any]]:
        """Raw daily bars for forecast/signal pipelines (cached lightly)."""
        resolved = resolve_symbol(symbol) or symbol
        cache_key = f"ohlcv_raw:{resolved}:{period}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        bars = await self.provider.get_ohlcv(symbol=resolved, interval="1d", period=period)
        # Serialize Decimals as strings for Redis
        serializable = []
        for b in bars:
            serializable.append(
                {
                    "date": b.get("date"),
                    "open": str(b["open"]) if b.get("open") is not None else None,
                    "high": str(b["high"]) if b.get("high") is not None else None,
                    "low": str(b["low"]) if b.get("low") is not None else None,
                    "close": str(b["close"]) if b.get("close") is not None else None,
                    "volume": b.get("volume", 0),
                }
            )
        await cache_set(cache_key, serializable, ttl=CACHE_TTL_SECONDS)
        return serializable
