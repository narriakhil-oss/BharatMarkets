"""Technical analysis and indicator schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IndicatorValues(BaseModel):
    """Calculated technical indicator values for a stock."""

    model_config = ConfigDict(from_attributes=True)

    sma_20: Optional[Decimal] = Field(None, description="20-day Simple Moving Average")
    sma_50: Optional[Decimal] = Field(None, description="50-day Simple Moving Average")
    sma_200: Optional[Decimal] = Field(None, description="200-day Simple Moving Average")
    ema_20: Optional[Decimal] = Field(None, description="20-day Exponential Moving Average")
    rsi_14: Optional[Decimal] = Field(None, description="14-day Relative Strength Index")
    macd_line: Optional[Decimal] = Field(None, description="MACD Line (12 - 26 EMA)")
    macd_signal: Optional[Decimal] = Field(None, description="MACD Signal Line (9 EMA of MACD)")
    macd_histogram: Optional[Decimal] = Field(None, description="MACD Histogram (MACD - Signal)")
    bollinger_upper: Optional[Decimal] = Field(None, description="Bollinger Band Upper (20, 2σ)")
    bollinger_middle: Optional[Decimal] = Field(None, description="Bollinger Band Middle (20 SMA)")
    bollinger_lower: Optional[Decimal] = Field(None, description="Bollinger Band Lower (20, 2σ)")
    high_52w: Optional[Decimal] = Field(None, description="52-week highest traded price")
    low_52w: Optional[Decimal] = Field(None, description="52-week lowest traded price")
    volume_current: Optional[int] = Field(None, description="Most recent session volume")
    volume_avg_20d: Optional[int] = Field(None, description="20-day average trading volume")


class TrendAnalysis(BaseModel):
    """Rule-based trend classification and plain English rationales."""

    model_config = ConfigDict(from_attributes=True)

    trend: str = Field(..., description="Overall trend: Bullish, Bearish, or Sideways")
    strength: str = Field(..., description="Trend conviction: Strong, Moderate, or Weak")
    score: Optional[int] = Field(None, description="Composite score based on technical rules")
    reasons: List[str] = Field(default_factory=list, description="Plain English explanations of technical signals")


class AnalysisResponse(BaseModel):
    """Complete technical analysis response payload."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="Stock symbol (e.g. RELIANCE.NS)")
    name: str = Field(..., description="Company name")
    ltp: Decimal = Field(..., description="Last traded price")
    indicators: IndicatorValues = Field(..., description="Computed technical indicators")
    trend: TrendAnalysis = Field(..., description="Trend analysis and rationales")
    analyzed_at: datetime = Field(..., description="UTC timestamp of the analysis calculation")
