"""
Rate Limiting Middleware
========================
Limits the number of requests from a single IP address.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timedelta
import time
from app.core.cache import redis_client
from app.core.config import settings
from app.core.logger import logger

# Rate limit exceptions (no rate limiting)
NO_LIMIT_PATHS = [
    "/api/v1/health",
    "/api/v1/webhooks/stripe",
    "/api/v1/webhooks/opay",
]

# Rate limit configurations per path prefix
RATE_LIMITS = {
    "/api/v1/auth/login": {"requests": 10, "period": 60},  # 10 per minute
    "/api/v1/auth/register": {"requests": 5, "period": 3600},  # 5 per hour
    "/api/v1/auth/forgot-password": {"requests": 3, "period": 3600},  # 3 per hour
    "/api/v1/payments/": {"requests": 20, "period": 60},  # 20 per minute
    "/api/v1/books/": {"requests": 100, "period": 60},  # 100 per minute
    "default": {"requests": 60, "period": 60},  # 60 per minute
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request rates per IP address.
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip rate limiting for webhooks and health checks
        if path in NO_LIMIT_PATHS:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Determine rate limit config
        rate_config = self._get_rate_config(path)
        
        # Create rate limit key
        key = f"rate_limit:{client_ip}:{path}"
        
        # Get current count
        current = await redis_client.get(key)
        
        if current is None:
            # First request in the period
            await redis_client.setex(key, rate_config["period"], 1)
            return await call_next(request)
        
        count = int(current)
        
        if count >= rate_config["requests"]:
            # Rate limit exceeded
            ttl = await redis_client.ttl(key)
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                headers={
                    "X-RateLimit-Limit": str(rate_config["requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + ttl)),
                    "Retry-After": str(ttl),
                }
            )
        
        # Increment counter
        await redis_client.incr(key)
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        remaining = rate_config["requests"] - (count + 1)
        response.headers["X-RateLimit-Limit"] = str(rate_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + await redis_client.ttl(key)))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_rate_config(self, path: str) -> dict:
        """Get rate limit configuration for a path."""
        for prefix, config in RATE_LIMITS.items():
            if path.startswith(prefix):
                return config
        return RATE_LIMITS["default"]
