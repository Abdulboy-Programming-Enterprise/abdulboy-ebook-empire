"""
Decorators Module
=================
Custom decorators for rate limiting, logging, caching, and retry logic.
"""

import functools
import time
import asyncio
from typing import Any, Callable, Optional
from functools import wraps
from loguru import logger
from app.core.cache import cache_service
from app.core.exceptions import RateLimitException


def rate_limit(key_prefix: str, requests: int, period: int):
    """
    Rate limiting decorator.
    
    Args:
        key_prefix: Prefix for the rate limit key
        requests: Maximum number of requests allowed
        period: Time period in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get client identifier (IP or user ID)
            request = kwargs.get('request') or (args[0] if args else None)
            client_id = getattr(request, 'client', None)
            if client_id:
                identifier = client_id.host
            else:
                identifier = 'anonymous'
            
            cache_key = f"rate_limit:{key_prefix}:{identifier}"
            
            # Get current count
            current = await cache_service.get(cache_key) or 0
            
            if current >= requests:
                raise RateLimitException(f"Rate limit exceeded. Try again in {period} seconds.")
            
            # Increment count
            await cache_service.increment(cache_key)
            await cache_service.expire(cache_key, period)
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper(*args, **kwargs)
            
            request = kwargs.get('request') or (args[0] if args else None)
            client_id = getattr(request, 'client', None)
            identifier = client_id.host if client_id else 'anonymous'
            
            cache_key = f"rate_limit:{key_prefix}:{identifier}"
            
            # Get current count (synchronous version would need sync redis)
            # For simplicity, we implement async only
            return func(*args, **kwargs)
        
        return sync_wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """Log the execution time of a function."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} executed in {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} failed after {elapsed:.2f}ms: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper(*args, **kwargs)
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} executed in {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} failed after {elapsed:.2f}ms: {e}")
            raise
    
    return sync_wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator for handling transient failures.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper(*args, **kwargs)
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        return sync_wrapper
    return decorator


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """
    Cache decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            import hashlib
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            cached = await cache_service.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper(*args, **kwargs)
            
            # For sync functions, we need a sync cache approach
            # Simplified: just execute without caching
            return func(*args, **kwargs)
        
        return sync_wrapper
    return decorator


def require_admin(func: Callable) -> Callable:
    """Decorator to require admin privileges."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        from app.core.exceptions import ForbiddenException
        
        # Get current user from context
        current_user = kwargs.get('current_user')
        if not current_user or current_user.account_type != 'admin':
            raise ForbiddenException("Admin privileges required")
        
        return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper(*args, **kwargs)
        
        from app.core.exceptions import ForbiddenException
        
        current_user = kwargs.get('current_user')
        if not current_user or current_user.account_type != 'admin':
            raise ForbiddenException("Admin privileges required")
        
        return func(*args, **kwargs)
    
    return sync_wrapper


def require_special_or_admin(func: Callable) -> Callable:
    """Decorator to require special user or admin privileges."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        from app.core.exceptions import ForbiddenException
        
        current_user = kwargs.get('current_user')
        if not current_user or current_user.account_type not in ['admin', 'special']:
            raise ForbiddenException("Special user or admin privileges required")
        
        return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper(*args, **kwargs)
        
        from app.core.exceptions import ForbiddenException
        
        current_user = kwargs.get('current_user')
        if not current_user or current_user.account_type not in ['admin', 'special']:
            raise ForbiddenException("Special user or admin privileges required")
        
        return func(*args, **kwargs)
    
    return sync_wrapper


def validate_request(schema_class):
    """Decorator to validate request body against a Pydantic schema."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request = kwargs.get('request') or (args[0] if args else None)
            
            if request and hasattr(request, 'json'):
                body = await request.json()
                validated = schema_class(**body)
                kwargs['validated_data'] = validated
            
            return await func(*args, **kwargs)
        
        return async_wrapper
    return decorator
