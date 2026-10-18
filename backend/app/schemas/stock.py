"""Stock entity and search Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.market import StockQuoteResponse


class StockSearchResult(BaseModel):
    """Autocomplete or search match result for a stock."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="Stock symbol (e.g. RELIANCE.NS)")
    name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Industry sector")
    exchange: str = Field(default="NSE", description="Exchange code")


class FundamentalResponse(BaseModel):
    """Company fundamental metrics and valuation ratios."""

    model_config = ConfigDict(from_attributes=True)

    symbol: Optional[str] = Field(None, description="Stock ticker symbol")
    market_cap: Optional[Decimal] = Field(None, description="Market Capitalization in INR")
    pe_ratio: Optional[Decimal] = Field(None, description="Trailing Price-to-Earnings ratio")
    pb_ratio: Optional[Decimal] = Field(None, description="Price-to-Book ratio")
    eps: Optional[Decimal] = Field(None, description="Trailing 12-month Earnings Per Share in INR")
    roe: Optional[Decimal] = Field(None, description="Return on Equity percentage")
    dividend_yield: Optional[Decimal] = Field(None, description="Dividend Yield percentage")
    face_value: Optional[Decimal] = Field(None, description="Face Value per share in INR")
    book_value: Optional[Decimal] = Field(None, description="Book Value per share in INR")
    updated_at: Optional[datetime] = Field(None, description="UTC timestamp of metrics update")


class StockDetailResponse(BaseModel):
    """Full stock profile including metadata, snapshot, and fundamentals."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    isin: Optional[str] = Field(None, description="ISIN code")
    sector: Optional[str] = Field(None, description="Industry sector")
    industry: Optional[str] = Field(None, description="Specific industry classification")
    exchange: str = Field(default="NSE", description="Primary exchange")
    lot_size: int = Field(default=1, description="Standard market lot size")
    tick_size: Decimal = Field(default=Decimal("0.05"), description="Minimum price movement (tick size)")
    circuit_limit_pct: Optional[int] = Field(None, description="Daily circuit breaker limit percentage")
    snapshot: Optional[StockQuoteResponse] = Field(None, description="Latest market price snapshot")
    fundamentals: Optional[FundamentalResponse] = Field(None, description="Fundamental valuation ratios")
