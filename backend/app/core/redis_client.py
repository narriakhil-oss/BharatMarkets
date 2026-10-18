"""Async Redis client and cache helper functions."""

import json
from decimal import Decimal
from datetime import date, datetime
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.config import get_settings
from app.core.market_hours import get_cache_ttl

settings = get_settings()

# Module-level Redis client instance
redis_client: Optional[Redis] = None


class DecimalDateEncoder(json.JSONEncoder):
    """Custom JSON encoder supporting Decimal, datetime, and date objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


async def init_redis() -> Redis:
    """Initialize Redis connection pool."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )
    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def get_redis() -> Redis:
    """FastAPI dependency or internal accessor for Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = await init_redis()
    return redis_client


async def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve and deserialize a JSON-cached object from Redis.

    Args:
        key: Cache key.

    Returns:
        Deserialized object or None if key is absent or on error.
    """
    try:
        client = await get_redis()
        val = await client.get(key)
        if val is None:
            return None
        return json.loads(val)
    except Exception:
        # Cache failure should not break critical application paths
        return None


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Serialize and store an object in Redis with an expiration TTL.

    Args:
        key: Cache key.
        value: Serializable data object.
        ttl: Expiration in seconds. If None, dynamically calculated based on market hours.

    Returns:
        bool: True if cached successfully, False otherwise.
    """
    try:
        client = await get_redis()
        if ttl is None:
            ttl = get_cache_ttl()

        payload = json.dumps(value, cls=DecimalDateEncoder)
        await client.set(key, payload, ex=ttl)
        return True
    except Exception:
        return False


async def cache_delete(key: str) -> bool:
    """
    Remove a key from Redis.

    Args:
        key: Cache key to delete.

    Returns:
        bool: True if delete succeeded, False otherwise.
    """
    try:
        client = await get_redis()
        await client.delete(key)
        return True
    except Exception:
        return False


async def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching a glob pattern.

    Args:
        pattern: Pattern string (e.g. 'stock:*').

    Returns:
        int: Number of deleted keys.
    """
    try:
        client = await get_redis()
        keys = await client.keys(pattern)
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception:
        return 0
