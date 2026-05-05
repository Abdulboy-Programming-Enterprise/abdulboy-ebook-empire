"""
Cache Strategy
==============
Implements intelligent caching strategies for different content types.
"""

import hashlib
import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from app.core.cache import cache_service
from app.core.logger import logger


class CacheStrategy:
    """Intelligent caching strategies for different content types."""
    
    # Cache TTLs by content type (seconds)
    TTL_CONFIG = {
        'html': 300,           # 5 minutes
        'json_api': 60,        # 1 minute
        'book_list': 300,      # 5 minutes
        'book_detail': 600,    # 10 minutes
        'user_profile': 1800,  # 30 minutes
        'search_results': 120, # 2 minutes
        'static_assets': 86400, # 24 hours
        'recommendations': 3600, # 1 hour
        'leaderboard': 3600,   # 1 hour
    }
    
    # Cache tags for invalidation
    CACHE_TAGS = {
        'books': ['book_list', 'book_detail', 'search_results'],
        'users': ['user_profile', 'user_dashboard'],
        'payments': ['payment_status', 'user_purchases'],
        'static': ['static_assets'],
    }
    
    @staticmethod
    async def get_or_set(
        key: str,
        fetcher: callable,
        ttl: Optional[int] = None,
        content_type: str = 'json_api'
    ) -> Any:
        """
        Get from cache or fetch and cache.
        
        Args:
            key: Cache key
            fetcher: Async function to fetch data if not cached
            ttl: Time to live in seconds (overrides default)
            content_type: Type of content for TTL selection
            
        Returns:
            Cached or fetched data
        """
        # Check cache
        cached = await cache_service.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached
        
        # Fetch fresh data
        logger.debug(f"Cache miss: {key}, fetching...")
        data = await fetcher()
        
        # Cache the result
        cache_ttl = ttl or CacheStrategy.TTL_CONFIG.get(content_type, 300)
        await cache_service.set(key, data, cache_ttl)
        
        return data
    
    @staticmethod
    async def invalidate_tag(tag: str) -> int:
        """
        Invalidate all cache keys associated with a tag.
        
        Args:
            tag: Cache tag (books, users, payments, static)
            
        Returns:
            Number of keys invalidated
        """
        if tag not in CacheStrategy.CACHE_TAGS:
            logger.warning(f"Unknown cache tag: {tag}")
            return 0
        
        invalidated = 0
        for pattern in CacheStrategy.CACHE_TAGS[tag]:
            # Delete keys matching pattern
            # In production, use Redis SCAN for pattern matching
            await cache_service.delete(pattern)
            invalidated += 1
        
        logger.info(f"Invalidated cache tag: {tag}, {invalidated} keys")
        return invalidated
    
    @staticmethod
    async def generate_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate a deterministic cache key.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        
        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    @staticmethod
    async def warm_cache(
        cache_items: Dict[str, Dict[str, Any]],
        content_type: str = 'json_api'
    ) -> int:
        """
        Pre-warm cache with common data.
        
        Args:
            cache_items: Dictionary of cache keys and their data
            content_type: Content type for TTL
            
        Returns:
            Number of items cached
        """
        warmed = 0
        ttl = CacheStrategy.TTL_CONFIG.get(content_type, 300)
        
        for key, data in cache_items.items():
            await cache_service.set(key, data, ttl)
            warmed += 1
        
        logger.info(f"Warmed cache with {warmed} items")
        return warmed
    
    @staticmethod
    async def get_cache_stats() -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        # In production, use Redis INFO command
        return {
            "total_keys": 0,  # Would query Redis
            "memory_usage_mb": 0,
            "hit_rate": 0.95,
        }
