"""
CORS Middleware
===============
Cross-Origin Resource Sharing configuration for the API.
"""

from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from app.core.config import settings


def setup_cors(app):
    """
    Configure CORS for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-Request-ID",
            "X-Forwarded-For",
        ],
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Request-ID",
        ],
        max_age=86400,  # 24 hours
    )
