"""Market and quote related Pydantic response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MarketStatusResponse(BaseModel):
    """Current market status payload."""

    model_config = ConfigDict(from_attributes=True)

    is_open: bool = Field(..., description="Whether regular trading is currently active")
    status: str = Field(..., description="Short status code (OPEN, PRE_OPEN, CLOSED, WEEKEND, HOLIDAY)")
    status_text: str = Field(..., description="Human-readable description of current market status")
    current_time_ist: str = Field(..., description="Current timestamp in Indian Standard Time (ISO format)")
    next_open_ist: str = Field(..., description="Next market opening time in IST (ISO format)")
    exchange: str = Field(default="NSE", description="Exchange code")
    last_updated_ist: Optional[str] = Field(None, description="Last data update time in IST")


class IndexResponse(BaseModel):
    """Benchmark index quote payload."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="Ticker symbol (e.g. ^NSEI)")
    display_name: str = Field(..., description="Display label (e.g. NIFTY 50)")
    ltp: Decimal = Field(..., description="Last traded price")
    change: Decimal = Field(..., description="Net absolute price change from previous close")
    change_pct: Decimal = Field(..., description="Percentage change from previous close")
    exchange: str = Field(default="NSE", description="Exchange identifier")
    day_high: Optional[Decimal] = Field(None, description="Intraday high")
    day_low: Optional[Decimal] = Field(None, description="Intraday low")


class StockQuoteResponse(BaseModel):
    """Real-time quote snapshot for an individual stock."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="NSE/BSE stock ticker symbol (e.g. RELIANCE.NS)")
    name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Industry sector")
    ltp: Decimal = Field(..., description="Last traded price")
    prev_close: Decimal = Field(..., description="Previous session closing price")
    change: Decimal = Field(..., description="Absolute price change")
    change_pct: Decimal = Field(..., description="Percentage price change")
    day_high: Optional[Decimal] = Field(None, description="Intraday high price")
    day_low: Optional[Decimal] = Field(None, description="Intraday low price")
    high_52w: Optional[Decimal] = Field(None, description="52-week high price")
    low_52w: Optional[Decimal] = Field(None, description="52-week low price")
    volume: Optional[int] = Field(None, description="Total traded volume")
    exchange: str = Field(default="NSE", description="Exchange code")
    updated_at: datetime = Field(..., description="Snapshot timestamp in UTC")


class GainerLoserResponse(BaseModel):
    """List of top market gainers or losers."""

    model_config = ConfigDict(from_attributes=True)

    items: List[StockQuoteResponse] = Field(..., description="List of stock quote objects")


class SectorPerformanceResponse(BaseModel):
    """Aggregate market performance by sector."""

    model_config = ConfigDict(from_attributes=True)

    sector: str = Field(..., description="Sector name")
    change_pct: Decimal = Field(..., description="Average percentage change across sector stocks")
    stock_count: int = Field(..., description="Total number of constituent stocks tracked in this sector")


class OHLCVResponse(BaseModel):
    """Historical or intraday OHLCV candlestick bar."""

    model_config = ConfigDict(from_attributes=True)

    date: Optional[str] = Field(None, description="Date of daily bar (YYYY-MM-DD)")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of intraday bar in UTC")
    open: Decimal = Field(..., description="Opening price")
    high: Decimal = Field(..., description="Highest price during bar")
    low: Decimal = Field(..., description="Lowest price during bar")
    close: Decimal = Field(..., description="Closing price")
    volume: int = Field(..., description="Total volume traded during bar")


class MarketBreadthResponse(BaseModel):
    """Market breadth: advances vs declines."""

    model_config = ConfigDict(from_attributes=True)

    advances: int = Field(..., description="Number of stocks with positive change")
    declines: int = Field(..., description="Number of stocks with negative change")
    unchanged: int = Field(..., description="Number of stocks with no change")
    total: int = Field(..., description="Total stocks analyzed")
    advance_decline_ratio: Optional[Decimal] = Field(None, description="Advance/Decline ratio")
