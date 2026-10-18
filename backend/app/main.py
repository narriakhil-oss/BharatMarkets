"""FastAPI main application entrypoint for BharatMarkets API."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import ws_router
from app.api.v1 import analysis_router, chat_router, market_router, stocks_router
from app.config import get_settings
from app.core import market_hours
from app.core.database import engine
from app.core.exceptions import (
    MarketDataError,
    RateLimitExceededError,
    StockNotFoundError,
    general_exception_handler,
    market_data_error_handler,
    rate_limit_exceeded_handler,
    stock_not_found_handler,
)
from app.core.rate_limit import limiter
from app.core.redis_client import close_redis, init_redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bharatmarkets")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Modern lifespan context manager managing startup and graceful shutdown tasks.
    Initializes Redis connection pool, loads trading calendars, and releases DB connections.
    """
    logger.info("Starting BharatMarkets API [%s mode]...", settings.ENVIRONMENT)

    # 1. Initialize Redis connection pool
    try:
        await init_redis()
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.warning("Redis initial connection warning: %s", e)

    # 2. Pre-load NSE holiday schedule
    try:
        market_hours.load_holidays()
        logger.info("Loaded trading holidays schedule.")
    except Exception as e:
        logger.warning("Error loading trading calendar: %s", e)

    yield

    # Shutdown sequence
    logger.info("Shutting down BharatMarkets API...")
    try:
        await close_redis()
        logger.info("Closed Redis connection.")
    except Exception as e:
        logger.warning("Error closing Redis: %s", e)

    try:
        await engine.dispose()
        logger.info("Disposed SQLAlchemy database engine.")
    except Exception as e:
        logger.warning("Error disposing DB engine: %s", e)


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="BharatMarkets API",
        description=(
            "Public educational API for Indian stock market tracking and analysis. "
            "Real-time quotes, technical indicators, and market data for NSE & BSE stocks. "
            "Built purely for educational purposes — all monetary values use Decimal precision."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Attach limiter to application state
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom Exception Handlers
    app.add_exception_handler(StockNotFoundError, stock_not_found_handler)
    app.add_exception_handler(MarketDataError, market_data_error_handler)
    app.add_exception_handler(RateLimitExceededError, rate_limit_exceeded_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Health check endpoint
    @app.get(
        "/health",
        tags=["System"],
        summary="Service Health Check",
        description="Verify service availability, environment, and system timestamp.",
    )
    async def health_check() -> JSONResponse:
        """Return system health status."""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "service": "BharatMarkets API",
                "environment": settings.ENVIRONMENT,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    # Register API v1 Routers
    app.include_router(market_router, prefix="/api/v1")
    app.include_router(stocks_router, prefix="/api/v1")
    app.include_router(analysis_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

    # Register WebSocket Router
    app.include_router(ws_router)

    return app


app = create_app()
