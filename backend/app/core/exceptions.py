"""Custom exceptions and FastAPI exception handlers."""

import logging
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class BharatMarketsException(Exception):
    """Base application exception for BharatMarkets."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class StockNotFoundError(BharatMarketsException):
    """Raised when a requested stock symbol cannot be found."""

    def __init__(self, symbol: str, message: Optional[str] = None):
        msg = message or f"Stock with symbol '{symbol}' was not found in BharatMarkets database."
        super().__init__(msg, details={"symbol": symbol})
        self.symbol = symbol


class MarketDataError(BharatMarketsException):
    """Raised when external market data providers (e.g. yfinance) fail or return invalid data."""

    def __init__(self, message: str = "Market data provider service temporarily unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


class RateLimitExceededError(BharatMarketsException):
    """Raised when client exceeds rate limits."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later.", retry_after: int = 60):
        super().__init__(message, details={"retry_after": retry_after})
        self.retry_after = retry_after


# FastAPI Exception Handlers
async def stock_not_found_handler(request: Request, exc: StockNotFoundError) -> JSONResponse:
    """Handle StockNotFoundError with 404 status."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "StockNotFound",
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def market_data_error_handler(request: Request, exc: MarketDataError) -> JSONResponse:
    """Handle MarketDataError with 502 status."""
    logger.error("MarketDataError encountered: %s", exc.message)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": "MarketDataError",
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceededError) -> JSONResponse:
    """Handle RateLimitExceededError with 429 status."""
    headers = {"Retry-After": str(exc.retry_after)} if hasattr(exc, "retry_after") else {}
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers=headers,
        content={
            "error": "RateLimitExceeded",
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled internal server exceptions with 500 status."""
    logger.exception("Unhandled server error: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the request.",
            "path": str(request.url.path),
        },
    )
