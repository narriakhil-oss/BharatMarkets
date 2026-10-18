"""Technical analysis API routes."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import MarketDataError, StockNotFoundError
from app.dependencies import get_db, get_market_data_provider
from app.models.stock import Stock
from app.providers.base import MarketDataProvider
from app.schemas.analysis import (
    AnalysisResponse,
    IndicatorValues,
    TrendAnalysis,
)
from app.services.indicator_service import IndicatorService

router = APIRouter(prefix="/stocks", tags=["Analysis"])


def normalize_symbol(symbol: str) -> str:
    """Normalize symbol to uppercase and append .NS if exchange suffix is omitted."""
    sym = symbol.strip().upper()
    if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
        return f"{sym}.NS"
    return sym


@router.get(
    "/{symbol}/analysis",
    response_model=AnalysisResponse,
    summary="Get full technical analysis and trend evaluation",
    description="Calculates SMA (20/50/200), EMA 20, RSI 14, MACD, Bollinger Bands, and produces an educational trend analysis with clear explanations.",
)
async def get_stock_analysis(
    symbol: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: Annotated[MarketDataProvider, Depends(get_market_data_provider)],
) -> AnalysisResponse:
    """Perform technical indicator calculation and trend evaluation."""
    norm_symbol = normalize_symbol(symbol)

    stmt = (
        select(Stock)
        .options(selectinload(Stock.snapshot))
        .filter(or_(Stock.symbol == norm_symbol, Stock.symbol == symbol.upper()))
    )
    res = await db.execute(stmt)
    stock = res.scalar_one_or_none()

    if not stock:
        raise StockNotFoundError(symbol)

    # 1. Fetch 1 year of daily OHLCV candlestick data
    bars = await provider.get_ohlcv(symbol=stock.symbol, interval="1d", period="1y")
    if not bars:
        raise MarketDataError(
            f"Insufficient historical price data available to analyze {stock.symbol}."
        )

    # Extract price and volume series (chronological order)
    prices: List[Decimal] = [b["close"] for b in bars]
    highs: List[Decimal] = [b["high"] for b in bars]
    lows: List[Decimal] = [b["low"] for b in bars]
    volumes: List[int] = [b["volume"] for b in bars]

    ltp = stock.snapshot.ltp if stock.snapshot else prices[-1]

    # 2. Calculate Indicators
    sma_20 = IndicatorService.calculate_sma(prices, 20)
    sma_50 = IndicatorService.calculate_sma(prices, 50)
    sma_200 = IndicatorService.calculate_sma(prices, 200)
    ema_20 = IndicatorService.calculate_ema(prices, 20)
    rsi_14 = IndicatorService.calculate_rsi(prices, 14)
    macd_line, macd_signal, macd_hist = IndicatorService.calculate_macd(prices, 12, 26, 9)
    bollinger_upper, bollinger_middle, bollinger_lower = (
        IndicatorService.calculate_bollinger_bands(prices, 20, 2)
    )

    # 3. 52-week High/Low
    high_52w = max(highs) if highs else None
    low_52w = min(lows) if lows else None

    # 4. Volume comparison vs 20-day average
    volume_current = volumes[-1] if volumes else 0
    volume_avg_20d: int = 0
    if len(volumes) >= 20:
        volume_avg_20d = int(sum(volumes[-20:]) / 20)
    elif volumes:
        volume_avg_20d = int(sum(volumes) / len(volumes))

    indicators = IndicatorValues(
        sma_20=sma_20,
        sma_50=sma_50,
        sma_200=sma_200,
        ema_20=ema_20,
        rsi_14=rsi_14,
        macd_line=macd_line,
        macd_signal=macd_signal,
        macd_histogram=macd_hist,
        bollinger_upper=bollinger_upper,
        bollinger_middle=bollinger_middle,
        bollinger_lower=bollinger_lower,
        high_52w=high_52w,
        low_52w=low_52w,
        volume_current=volume_current,
        volume_avg_20d=volume_avg_20d if volume_avg_20d > 0 else None,
    )

    # 5. Trend Analysis
    trend = IndicatorService.analyze_trend(
        ltp=ltp,
        sma_20=sma_20,
        sma_50=sma_50,
        sma_200=sma_200,
        ema_20=ema_20,
        rsi=rsi_14,
        macd_line=macd_line,
        macd_signal=macd_signal,
        bollinger_upper=bollinger_upper,
        bollinger_lower=bollinger_lower,
        high_52w=high_52w,
        low_52w=low_52w,
        volume=volume_current,
        volume_avg=volume_avg_20d,
    )

    return AnalysisResponse(
        symbol=stock.symbol,
        name=stock.name,
        ltp=ltp,
        indicators=indicators,
        trend=trend,
        analyzed_at=datetime.now(timezone.utc),
    )
