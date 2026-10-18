"""Yahoo Finance market data provider implementation."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import yfinance as yf

from app.core.exceptions import MarketDataError
from app.providers.base import MarketDataProvider

logger = logging.getLogger(__name__)


def to_decimal(val: Any, decimals: int = 4) -> Optional[Decimal]:
    """Safely convert numeric values, floats, or strings to Decimal."""
    if val is None:
        return None
    try:
        if isinstance(val, (int, str)):
            return Decimal(str(val))
        # Handle float and numpy floats
        float_val = float(val)
        if float_val != float_val:  # NaN check
            return None
        return Decimal(f"{float_val:.{decimals}f}")
    except Exception:
        return None


def to_int(val: Any) -> Optional[int]:
    """Safely convert value to integer."""
    if val is None:
        return None
    try:
        float_val = float(val)
        if float_val != float_val:
            return None
        return int(float_val)
    except Exception:
        return None


class YFinanceProvider(MarketDataProvider):
    """Market data provider backed by yfinance with asynchronous thread execution."""

    def _sync_get_quote(self, symbol: str) -> Dict[str, Any]:
        """Synchronous quote fetch via yfinance."""
        ticker = yf.Ticker(symbol)

        ltp: Optional[Decimal] = None
        prev_close: Optional[Decimal] = None
        day_high: Optional[Decimal] = None
        day_low: Optional[Decimal] = None
        high_52w: Optional[Decimal] = None
        low_52w: Optional[Decimal] = None
        volume: Optional[int] = None

        # 1. Try fast_info first (fastest and most reliable in modern yfinance)
        try:
            fast = getattr(ticker, "fast_info", None)
            if fast:
                ltp = to_decimal(fast.last_price)
                prev_close = to_decimal(fast.previous_close)
                day_high = to_decimal(fast.day_high)
                day_low = to_decimal(fast.day_low)
                high_52w = to_decimal(fast.year_high)
                low_52w = to_decimal(fast.year_low)
                volume = to_int(fast.last_volume)
        except Exception as e:
            logger.debug("Fast info failed for %s: %s", symbol, e)

        # 2. Try regular info if fast_info missing primary price
        if ltp is None or prev_close is None:
            try:
                info = ticker.info or {}
                ltp = to_decimal(
                    info.get("currentPrice")
                    or info.get("regularMarketPrice")
                    or info.get("ask")
                    or info.get("bid")
                )
                prev_close = to_decimal(
                    info.get("previousClose") or info.get("regularMarketPreviousClose")
                )
                day_high = day_high or to_decimal(info.get("dayHigh") or info.get("regularMarketDayHigh"))
                day_low = day_low or to_decimal(info.get("dayLow") or info.get("regularMarketDayLow"))
                high_52w = high_52w or to_decimal(info.get("fiftyTwoWeekHigh"))
                low_52w = low_52w or to_decimal(info.get("fiftyTwoWeekLow"))
                volume = volume or to_int(info.get("volume") or info.get("regularMarketVolume"))
            except Exception as e:
                logger.debug("Info fetch failed for %s: %s", symbol, e)

        # 3. Fallback to 5-day historical bars
        if ltp is None or prev_close is None:
            try:
                hist = ticker.history(period="5d", interval="1d")
                if not hist.empty:
                    last_row = hist.iloc[-1]
                    ltp = to_decimal(last_row["Close"])
                    volume = to_int(last_row.get("Volume", 0))
                    day_high = day_high or to_decimal(last_row.get("High"))
                    day_low = day_low or to_decimal(last_row.get("Low"))

                    if len(hist) > 1:
                        prev_close = to_decimal(hist.iloc[-2]["Close"])
                    else:
                        prev_close = to_decimal(last_row["Open"])
            except Exception as e:
                logger.warning("History fallback failed for %s: %s", symbol, e)

        if ltp is None:
            raise MarketDataError(f"Could not retrieve quote price for symbol '{symbol}'.")

        if prev_close is None or prev_close == Decimal("0"):
            prev_close = ltp

        change = ltp - prev_close
        change_pct = (change / prev_close) * Decimal("100") if prev_close != Decimal("0") else Decimal("0.0000")

        return {
            "symbol": symbol,
            "ltp": ltp.quantize(Decimal("0.0001")),
            "prev_close": prev_close.quantize(Decimal("0.0001")),
            "change": change.quantize(Decimal("0.0001")),
            "change_pct": change_pct.quantize(Decimal("0.0001")),
            "day_high": day_high.quantize(Decimal("0.0001")) if day_high else None,
            "day_low": day_low.quantize(Decimal("0.0001")) if day_low else None,
            "high_52w": high_52w.quantize(Decimal("0.0001")) if high_52w else None,
            "low_52w": low_52w.quantize(Decimal("0.0001")) if low_52w else None,
            "volume": volume or 0,
            "updated_at": datetime.now(timezone.utc),
        }

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch quote asynchronously via thread pool."""
        return await asyncio.to_thread(self._sync_get_quote, symbol)

    def _sync_get_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        period: str = "1mo",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronously fetch candlestick history."""
        ticker = yf.Ticker(symbol)
        try:
            if start and end:
                df = ticker.history(interval=interval, start=start, end=end)
            else:
                df = ticker.history(interval=interval, period=period)
        except Exception as e:
            logger.error("Error fetching history for %s: %s", symbol, e)
            return []

        if df.empty:
            return []

        results: List[Dict[str, Any]] = []
        is_intraday = interval in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h")

        for idx, row in df.iterrows():
            open_p = to_decimal(row.get("Open"))
            high_p = to_decimal(row.get("High"))
            low_p = to_decimal(row.get("Low"))
            close_p = to_decimal(row.get("Close"))
            vol = to_int(row.get("Volume", 0)) or 0

            if None in (open_p, high_p, low_p, close_p):
                continue

            item: Dict[str, Any] = {
                "open": open_p.quantize(Decimal("0.0001")),
                "high": high_p.quantize(Decimal("0.0001")),
                "low": low_p.quantize(Decimal("0.0001")),
                "close": close_p.quantize(Decimal("0.0001")),
                "volume": vol,
            }

            if is_intraday:
                # Convert timestamp to UTC datetime
                ts: datetime = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                else:
                    ts = ts.astimezone(timezone.utc)
                item["timestamp"] = ts
                item["date"] = ts.strftime("%Y-%m-%d")
            else:
                # Daily bar date string
                d_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                item["date"] = d_str
                item["timestamp"] = None

            results.append(item)

        return results

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        period: str = "1mo",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch historical bars asynchronously."""
        return await asyncio.to_thread(
            self._sync_get_ohlcv, symbol, interval, period, start, end
        )

    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Placeholder for provider search — database search is preferred for NSE/BSE."""
        return []

    def _sync_get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Synchronously fetch company fundamentals."""
        ticker = yf.Ticker(symbol)
        try:
            info = ticker.info or {}
        except Exception as e:
            logger.warning("Failed to fetch fundamentals info for %s: %s", symbol, e)
            info = {}

        market_cap = to_decimal(info.get("marketCap"))
        pe_ratio = to_decimal(info.get("trailingPE") or info.get("forwardPE"))
        pb_ratio = to_decimal(info.get("priceToBook"))
        eps = to_decimal(info.get("trailingEps") or info.get("forwardEps"))

        roe_val = info.get("returnOnEquity")
        roe = to_decimal(roe_val * 100) if roe_val is not None else None

        div_yield_val = info.get("dividendYield")
        div_yield = to_decimal(div_yield_val * 100) if div_yield_val is not None else None

        book_val = to_decimal(info.get("bookValue"))

        return {
            "symbol": symbol,
            "market_cap": market_cap.quantize(Decimal("0.0001")) if market_cap else None,
            "pe_ratio": pe_ratio.quantize(Decimal("0.0001")) if pe_ratio else None,
            "pb_ratio": pb_ratio.quantize(Decimal("0.0001")) if pb_ratio else None,
            "eps": eps.quantize(Decimal("0.0001")) if eps else None,
            "roe": roe.quantize(Decimal("0.0001")) if roe else None,
            "dividend_yield": div_yield.quantize(Decimal("0.0001")) if div_yield else None,
            "face_value": None,
            "book_value": book_val.quantize(Decimal("0.0001")) if book_val else None,
            "updated_at": datetime.now(timezone.utc),
        }

    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fetch company fundamentals asynchronously."""
        return await asyncio.to_thread(self._sync_get_fundamentals, symbol)

    def _sync_get_index_data(self, symbol: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch index data synchronously."""
        quote = self._sync_get_quote(symbol)
        exchange = "BSE" if symbol.startswith("^BSE") else "NSE"
        return {
            "symbol": symbol,
            "display_name": display_name or symbol,
            "ltp": quote["ltp"],
            "change": quote["change"],
            "change_pct": quote["change_pct"],
            "exchange": exchange,
        }

    async def get_index_data(self, symbol: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch index quote asynchronously."""
        return await asyncio.to_thread(self._sync_get_index_data, symbol, display_name)

    async def get_bulk_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple quotes concurrently with throttling."""
        tasks = [self.get_quote(sym) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        quotes: List[Dict[str, Any]] = []
        for sym, res in zip(symbols, results):
            if isinstance(res, Exception):
                logger.warning("Bulk quote failed for %s: %s", sym, res)
            elif isinstance(res, dict):
                quotes.append(res)
        return quotes
