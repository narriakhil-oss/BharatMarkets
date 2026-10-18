"""Schemas for history, forecast, signal, and chat assistant payloads."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class PricePoint(BaseModel):
    """Single daily price point for charts."""

    model_config = ConfigDict(from_attributes=True)

    date: str
    close: Decimal


class HistorySummary(BaseModel):
    """Past price summary for a period."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: Optional[str] = None
    period: str
    start_price: Decimal
    end_price: Decimal
    change_pct: Decimal
    high: Decimal
    low: Decimal
    series: List[PricePoint] = Field(default_factory=list)


class ForecastPoint(BaseModel):
    """Predicted close with confidence band."""

    model_config = ConfigDict(from_attributes=True)

    date: str
    predicted: Decimal
    lower: Decimal
    upper: Decimal


class BacktestMetrics(BaseModel):
    """Walk-forward backtest metrics (no look-ahead)."""

    model_config = ConfigDict(from_attributes=True)

    mape_pct: Optional[Decimal] = None
    directional_accuracy_pct: Optional[Decimal] = None
    samples: int = 0
    method: str = "unknown"
    note: Optional[str] = None


class ForecastResult(BaseModel):
    """Forecast payload for charts and chat tools."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str
    horizon_days: int
    method: str
    history_tail: List[PricePoint] = Field(default_factory=list)
    forecast: List[ForecastPoint] = Field(default_factory=list)
    backtest: BacktestMetrics
    last_close: Optional[Decimal] = None
    forecast_change_pct: Optional[Decimal] = None


class SignalFactor(BaseModel):
    """Single scored factor in the signal breakdown."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    score: int
    detail: str


class PriceRange(BaseModel):
    """Indicative price range."""

    model_config = ConfigDict(from_attributes=True)

    low: Decimal
    high: Decimal


class SignalResult(BaseModel):
    """Buy/Sell/Hold signal with transparent scoring."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str
    signal: Literal["Buy", "Sell", "Hold"]
    score: int
    factors: List[SignalFactor] = Field(default_factory=list)
    entry_zone: Optional[PriceRange] = None
    stop_loss: Optional[PriceRange] = None
    atr14: Optional[Decimal] = None
    support: Optional[Decimal] = None
    resistance: Optional[Decimal] = None
    backtest: Optional[BacktestMetrics] = None
    ltp: Optional[Decimal] = None


class ChatMessage(BaseModel):
    """Single chat turn."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """POST /api/v1/chat body."""

    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = Field(None, description="Client session id for history")
    history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Optional client-side history (server keeps last 10 per session)",
    )


class ChatStructuredPayload(BaseModel):
    """Structured side-channel for charts/cards alongside streamed text."""

    history: Optional[HistorySummary] = None
    forecast: Optional[ForecastResult] = None
    signal: Optional[SignalResult] = None
    market_overview: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None


class SupportResistance(BaseModel):
    """Recent swing support and resistance levels."""

    model_config = ConfigDict(from_attributes=True)

    support: Optional[Decimal] = None
    resistance: Optional[Decimal] = None
    support_levels: List[Decimal] = Field(default_factory=list)
    resistance_levels: List[Decimal] = Field(default_factory=list)


class SessionMeta(BaseModel):
    """Lightweight session metadata."""

    session_id: str
    updated_at: datetime
