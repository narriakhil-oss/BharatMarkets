"""Async SQLAlchemy database configuration and session management."""

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Build engine lazily — only if DATABASE_URL is a valid postgres URL
_engine = None
_AsyncSessionLocal = None

_db_url = settings.DATABASE_URL or ""
_db_available = _db_url.startswith("postgresql")

if _db_available:
    try:
        _engine = create_async_engine(
            _db_url,
            echo=(settings.ENVIRONMENT == "development"),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        _AsyncSessionLocal = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    except Exception:
        _db_available = False

# Public references (may be None if DB is unavailable)
engine = _engine
AsyncSessionLocal = _AsyncSessionLocal


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """FastAPI dependency — yields an async DB session or None if DB unavailable."""
    if _AsyncSessionLocal is None:
        yield None
        return
    async with _AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
