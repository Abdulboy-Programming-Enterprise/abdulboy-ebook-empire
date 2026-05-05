"""
Compression Middleware
======================
Response compression using gzip or brotli.
"""

from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import gzip
import brotli


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to compress responses using gzip or brotli.
    """
    
    # Minimum size for compression (bytes)
    MIN_SIZE = 500
    
    # Content types to compress
    COMPRESS_TYPES = [
        "text/html",
        "text/css",
        "text/plain",
        "text/xml",
        "text/javascript",
        "application/javascript",
        "application/json",
        "application/xml",
        "application/rss+xml",
        "image/svg+xml",
    ]
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Skip compression for small responses
        if not hasattr(response, "body") or len(response.body) < self.MIN_SIZE:
            return response
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in self.COMPRESS_TYPES):
            return response
        
        # Check client supports compression
        accept_encoding = request.headers.get("accept-encoding", "")
        
        # Prefer brotli over gzip
        if "br" in accept_encoding:
            compressed_body = brotli.compress(response.body)
            response.headers["content-encoding"] = "br"
            response.body = compressed_body
        elif "gzip" in accept_encoding:
            compressed_body = gzip.compress(response.body)
            response.headers["content-encoding"] = "gzip"
            response.body = compressed_body
        
        # Update content length if present
        if "content-length" in response.headers:
            response.headers["content-length"] = str(len(response.body))
        
        response.headers["vary"] = "Accept-Encoding"
        
        return response


def setup_compression(app):
    """Setup compression for the FastAPI application."""
    app.add_middleware(GZipMiddleware, minimum_size=500)
