"""
App Package Initialization
==========================
Initializes the FastAPI application with all routes, middleware, and services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.core.logger import setup_logging
from app.core.database import engine, Base
from app.core.cache import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    setup_logging()
    await redis_client.ping()
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    await redis_client.close()
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Abdulboy Ebook Empire API",
        description="""
        World-class ebook platform API with AI recommendations, 
        multi-payment integration, and subscription services.
        """,
        version="1.0.0",
        docs_url="/api/docs" if settings.APP_DEBUG else None,
        redoc_url="/api/redoc" if settings.APP_DEBUG else None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted Host Middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    
    # Register Routers
    from app.api.v1 import (
        auth_routes,
        book_routes,
        payment_routes,
        admin_routes,
        subscription_routes,
        suggestion_routes,
        user_routes,
        booking_routes,
        analytics_routes,
        webhook_routes,
        health_routes,
        affiliate_routes,
        gamification_routes,
    )
    
    api_prefix = f"/api/{settings.API_VERSION}"
    
    app.include_router(auth_routes.router, prefix=api_prefix, tags=["Authentication"])
    app.include_router(book_routes.router, prefix=api_prefix, tags=["Books"])
    app.include_router(payment_routes.router, prefix=api_prefix, tags=["Payments"])
    app.include_router(admin_routes.router, prefix=api_prefix, tags=["Admin"])
    app.include_router(subscription_routes.router, prefix=api_prefix, tags=["Subscriptions"])
    app.include_router(suggestion_routes.router, prefix=api_prefix, tags=["Suggestions"])
    app.include_router(user_routes.router, prefix=api_prefix, tags=["Users"])
    app.include_router(booking_routes.router, prefix=api_prefix, tags=["Bookings"])
    app.include_router(analytics_routes.router, prefix=api_prefix, tags=["Analytics"])
    app.include_router(webhook_routes.router, prefix=api_prefix, tags=["Webhooks"])
    app.include_router(health_routes.router, prefix=api_prefix, tags=["Health"])
    app.include_router(affiliate_routes.router, prefix=api_prefix, tags=["Affiliate"])
    app.include_router(gamification_routes.router, prefix=api_prefix, tags=["Gamification"])
    
    return app
