"""
Request ID Middleware
=====================
Adds unique request IDs to each request for tracing and debugging.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.logger import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and attach a unique request ID to each request.
    """
    
    async def dispatch(self, request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in request state
        request.state.request_id = request_id
        
        # Add to logger context
        with logger.contextualize(request_id=request_id):
            # Process request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
        
        return response
