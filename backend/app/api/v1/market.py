"""Market routes for status, benchmark indices, top movers, sectors, and breadth."""

from typing import Annotated, List
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_market_service
from app.schemas.market import (
    IndexResponse,
    MarketBreadthResponse,
    MarketStatusResponse,
    SectorPerformanceResponse,
    StockQuoteResponse,
)
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["Market"])


@router.get(
    "/status",
    response_model=MarketStatusResponse,
    summary="Get current market status",
    description="Check whether Indian exchanges (NSE/BSE) are currently open or closed.",
)
async def get_status(
    market_service: Annotated[MarketService, Depends(get_market_service)],
) -> MarketStatusResponse:
    """Return live trading session status."""
    return market_service.get_market_status()


@router.get(
    "/indices",
    response_model=List[IndexResponse],
    summary="Get benchmark indices",
    description="Fetch latest quotes for NIFTY 50, SENSEX, BANK NIFTY, NIFTY IT.",
)
async def get_indices(
    market_service: Annotated[MarketService, Depends(get_market_service)],
) -> List[IndexResponse]:
    """Return quote details for benchmark indices."""
    return await market_service.get_indices()


@router.get(
    "/gainers",
    response_model=List[StockQuoteResponse],
    summary="Get top market gainers",
    description="Fetch top 10 stocks with the highest percentage price gain.",
)
async def get_top_gainers(
    market_service: Annotated[MarketService, Depends(get_market_service)],
) -> List[StockQuoteResponse]:
    """Return top 10 price gainers."""
    return await market_service.get_top_gainers(limit=10)


@router.get(
    "/losers",
    response_model=List[StockQuoteResponse],
    summary="Get top market losers",
    description="Fetch top 10 stocks with the largest percentage price drop.",
)
async def get_top_losers(
    market_service: Annotated[MarketService, Depends(get_market_service)],
) -> List[StockQuoteResponse]:
    """Return top 10 price losers."""
    return await market_service.get_top_losers(limit=10)


@router.get(
    "/sectors",
    response_model=List[SectorPerformanceResponse],
    summary="Get sector performance",
    description="Returns aggregate performance grouped by sector.",
)
async def get_sector_performance(
    market_service: Annotated[MarketService, Depends(get_market_service)],
    period: str = Query("1d", description="Period for performance: 1d, 1w, 1m"),
) -> List[SectorPerformanceResponse]:
    """Return sector performance summary."""
    return await market_service.get_sector_performance(period=period)


@router.get(
    "/breadth",
    response_model=MarketBreadthResponse,
    summary="Get market breadth",
    description="Returns advances vs declines count for NIFTY 100 stocks.",
)
async def get_market_breadth(
    market_service: Annotated[MarketService, Depends(get_market_service)],
) -> MarketBreadthResponse:
    """Return market breadth (advances, declines, unchanged)."""
    return await market_service.get_market_breadth()
