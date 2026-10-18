"""Abstract base class for market data providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MarketDataProvider(ABC):
    """Abstract interface for external or cached market data feeds."""

    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch the latest quote snapshot for a given stock symbol.

        Args:
            symbol: Ticker symbol (e.g. 'RELIANCE.NS').

        Returns:
            Dict containing ltp, prev_close, change, change_pct, day_high, day_low, 52w range, volume.
        """
        pass

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        period: str = "1mo",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical candlestick price bars.

        Args:
            symbol: Ticker symbol.
            interval: Candlestick interval (e.g. '1m', '5m', '1d', '1wk').
            period: Time window (e.g. '1d', '5d', '1mo', '3mo', '1y').
            start: Optional ISO date string start.
            end: Optional ISO date string end.

        Returns:
            List of OHLCV bar dictionaries.
        """
        pass

    @abstractmethod
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search stocks matching a name or ticker keyword.

        Args:
            query: Search query string.

        Returns:
            List of matching stock summary dicts.
        """
        pass

    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental company valuation and ratio data.

        Args:
            symbol: Ticker symbol.

        Returns:
            Dict containing market_cap, pe_ratio, pb_ratio, eps, roe, dividend_yield, etc.
        """
        pass

    @abstractmethod
    async def get_index_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch quote details for a market index (e.g. '^NSEI').

        Args:
            symbol: Index ticker.

        Returns:
            Dict containing symbol, display_name, ltp, change, change_pct, exchange.
        """
        pass

    @abstractmethod
    async def get_bulk_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch quotes for multiple tickers in batch.

        Args:
            symbols: List of ticker symbols.

        Returns:
            List of quote dictionaries.
        """
        pass
