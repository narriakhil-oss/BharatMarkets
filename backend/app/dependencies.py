"""Dependency injection providers for FastAPI."""

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis as _get_redis
from app.providers.yfinance_provider import YFinanceProvider
from app.services.chat_service import ChatService
from app.services.market_service import MarketService

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Provide an async database session, or None if DB is unavailable."""
    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        logger.debug("Database unavailable: %s", e)
        yield None


def get_market_data_provider() -> YFinanceProvider:
    """Provide YFinance market data provider."""
    return YFinanceProvider()


async def get_market_service() -> MarketService:
    """Provide MarketService with optional Redis."""
    redis = None
    try:
        redis = await _get_redis()
    except Exception:
        logger.debug("Redis unavailable, running without cache")

    provider = YFinanceProvider()
    return MarketService(db=None, redis=redis, provider=provider)


async def get_chat_service() -> ChatService:
    """Provide ChatService wired to yfinance + market overview tools."""
    provider = YFinanceProvider()
    market_service = await get_market_service()
    return ChatService(provider=provider, market_service=market_service)
