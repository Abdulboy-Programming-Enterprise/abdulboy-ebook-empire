"""
Cache Module
============
Redis cache management for session storage, rate limiting, and caching.
"""

import json
from typing import Optional, Any
import redis.asyncio as redis
from app.config import settings

# Redis client
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    password=settings.REDIS_PASSWORD,
)


async def get_redis():
    """Dependency for getting Redis client."""
    return redis_client


class CacheService:
    """Service for cache operations."""
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    
    @staticmethod
    async def set(key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        await redis_client.setex(key, ttl, json.dumps(value))
        return True
    
    @staticmethod
    async def delete(key: str) -> bool:
        """Delete key from cache."""
        await redis_client.delete(key)
        return True
    
    @staticmethod
    async def exists(key: str) -> bool:
        """Check if key exists in cache."""
        return await redis_client.exists(key) > 0
    
    @staticmethod
    async def increment(key: str, amount: int = 1) -> int:
        """Increment a counter in cache."""
        return await redis_client.incrby(key, amount)
    
    @staticmethod
    async def expire(key: str, ttl: int) -> bool:
        """Set expiration on a key."""
        return await redis_client.expire(key, ttl)


cache_service = CacheService()
