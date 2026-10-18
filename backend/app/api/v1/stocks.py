"""Stocks routes for search, real-time details, historical OHLCV, and fundamentals."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import StockNotFoundError
from app.dependencies import get_db, get_market_data_provider
from app.models.exchange import Exchange
from app.models.fundamental import Fundamental
from app.models.price import StockSnapshot
from app.models.stock import Stock
from app.providers.base import MarketDataProvider
from app.schemas.market import OHLCVResponse, StockQuoteResponse
from app.schemas.stock import (
    FundamentalResponse,
    StockDetailResponse,
    StockSearchResult,
)

router = APIRouter(prefix="/stocks", tags=["Stocks"])


def normalize_symbol(symbol: str) -> str:
    """Normalize symbol to uppercase and append .NS if exchange suffix is omitted."""
    sym = symbol.strip().upper()
    if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
        return f"{sym}.NS"
    return sym


@router.get(
    "/search",
    response_model=List[StockSearchResult],
    summary="Search stocks by symbol or company name",
    description="Autocomplete endpoint searching listed stocks in the database.",
)
async def search_stocks(
    q: Annotated[str, Query(min_length=1, max_length=50, description="Search query string")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[StockSearchResult]:
    """Search stocks matching query string in ticker or company name."""
    search_term = f"%{q.strip()}%"
    stmt = (
        select(Stock, Exchange)
        .join(Exchange, Stock.exchange_id == Exchange.id)
        .filter(
            Stock.is_active.is_(True),
            or_(
                Stock.symbol.ilike(search_term),
                Stock.name.ilike(search_term),
            ),
        )
        .limit(20)
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [
        StockSearchResult(
            symbol=stock.symbol,
            name=stock.name,
            sector=stock.sector,
            exchange=exchange.code,
        )
        for stock, exchange in rows
    ]


@router.get(
    "/{symbol}",
    response_model=StockDetailResponse,
    summary="Get stock details and latest quote",
    description="Fetches company metadata, latest snapshot quote, and fundamental valuation metrics.",
)
async def get_stock_detail(
    symbol: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: Annotated[MarketDataProvider, Depends(get_market_data_provider)],
) -> StockDetailResponse:
    """Fetch complete stock profile including live quote and fundamentals."""
    norm_symbol = normalize_symbol(symbol)

    stmt = (
        select(Stock)
        .options(
            selectinload(Stock.exchange),
            selectinload(Stock.snapshot),
            selectinload(Stock.fundamental),
        )
        .filter(
            or_(
                Stock.symbol == norm_symbol,
                Stock.symbol == symbol.upper(),
            )
        )
    )
    res = await db.execute(stmt)
    stock = res.scalar_one_or_none()

    if not stock:
        raise StockNotFoundError(symbol)

    exchange_code = stock.exchange.code if stock.exchange else "NSE"

    # Assemble snapshot quote
    snapshot_response: Optional[StockQuoteResponse] = None
    if stock.snapshot:
        snapshot_response = StockQuoteResponse(
            symbol=stock.symbol,
            name=stock.name,
            sector=stock.sector,
            ltp=stock.snapshot.ltp,
            prev_close=stock.snapshot.prev_close,
            change=stock.snapshot.change,
            change_pct=stock.snapshot.change_pct,
            day_high=stock.snapshot.day_high,
            day_low=stock.snapshot.day_low,
            high_52w=stock.snapshot.high_52w,
            low_52w=stock.snapshot.low_52w,
            volume=stock.snapshot.volume,
            exchange=exchange_code,
            updated_at=stock.snapshot.updated_at,
        )
    else:
        # Fallback to fetching live quote from provider
        try:
            live = await provider.get_quote(stock.symbol)
            snapshot_response = StockQuoteResponse(
                symbol=stock.symbol,
                name=stock.name,
                sector=stock.sector,
                ltp=live["ltp"],
                prev_close=live["prev_close"],
                change=live["change"],
                change_pct=live["change_pct"],
                day_high=live.get("day_high"),
                day_low=live.get("day_low"),
                high_52w=live.get("high_52w"),
                low_52w=live.get("low_52w"),
                volume=live.get("volume"),
                exchange=exchange_code,
                updated_at=live.get("updated_at", datetime.now(timezone.utc)),
            )
        except Exception:
            pass

    # Assemble fundamental metrics
    fundamental_response: Optional[FundamentalResponse] = None
    if stock.fundamental:
        fundamental_response = FundamentalResponse(
            symbol=stock.symbol,
            market_cap=stock.fundamental.market_cap,
            pe_ratio=stock.fundamental.pe_ratio,
            pb_ratio=stock.fundamental.pb_ratio,
            eps=stock.fundamental.eps,
            roe=stock.fundamental.roe,
            dividend_yield=stock.fundamental.dividend_yield,
            face_value=stock.fundamental.face_value,
            book_value=stock.fundamental.book_value,
            updated_at=stock.fundamental.updated_at,
        )

    return StockDetailResponse(
        symbol=stock.symbol,
        name=stock.name,
        isin=stock.isin,
        sector=stock.sector,
        industry=stock.industry,
        exchange=exchange_code,
        lot_size=stock.lot_size,
        tick_size=stock.tick_size,
        circuit_limit_pct=stock.circuit_limit_pct,
        snapshot=snapshot_response,
        fundamentals=fundamental_response,
    )


@router.get(
    "/{symbol}/ohlcv",
    response_model=List[OHLCVResponse],
    summary="Get candlestick OHLCV price series",
    description="Retrieve historical daily or intraday OHLCV candlestick bars for charting.",
)
async def get_stock_ohlcv(
    symbol: str,
    provider: Annotated[MarketDataProvider, Depends(get_market_data_provider)],
    interval: str = Query("1d", description="Bar interval: 1m, 5m, 15m, 1h, 1d, 1wk"),
    period: str = Query("1mo", description="Historical lookback window: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y"),
) -> List[OHLCVResponse]:
    """Retrieve OHLCV data series from provider."""
    norm_symbol = normalize_symbol(symbol)
    bars = await provider.get_ohlcv(symbol=norm_symbol, interval=interval, period=period)
    return [OHLCVResponse(**b) for b in bars]


@router.get(
    "/{symbol}/fundamentals",
    response_model=FundamentalResponse,
    summary="Get company fundamental ratios",
    description="Fetch financial ratios including P/E, P/B, EPS, ROE, Dividend Yield, Market Cap.",
)
async def get_stock_fundamentals(
    symbol: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: Annotated[MarketDataProvider, Depends(get_market_data_provider)],
) -> FundamentalResponse:
    """Fetch fundamental valuation ratios for a stock."""
    norm_symbol = normalize_symbol(symbol)

    stmt = (
        select(Stock)
        .options(selectinload(Stock.fundamental))
        .filter(or_(Stock.symbol == norm_symbol, Stock.symbol == symbol.upper()))
    )
    res = await db.execute(stmt)
    stock = res.scalar_one_or_none()

    if not stock:
        raise StockNotFoundError(symbol)

    if stock.fundamental:
        return FundamentalResponse(
            symbol=stock.symbol,
            market_cap=stock.fundamental.market_cap,
            pe_ratio=stock.fundamental.pe_ratio,
            pb_ratio=stock.fundamental.pb_ratio,
            eps=stock.fundamental.eps,
            roe=stock.fundamental.roe,
            dividend_yield=stock.fundamental.dividend_yield,
            face_value=stock.fundamental.face_value,
            book_value=stock.fundamental.book_value,
            updated_at=stock.fundamental.updated_at,
        )

    # Fallback to provider
    raw = await provider.get_fundamentals(norm_symbol)
    return FundamentalResponse(**raw)
