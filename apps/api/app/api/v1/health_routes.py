"""
Health Routes
=============
Health check endpoints for monitoring and load balancers.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from app.core.database import get_db
from app.core.cache import redis_client
from app.schemas.response import HealthResponse, StandardResponse
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
        services={}
    )


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
):
    """
    Readiness probe for Kubernetes.
    """
    services_status = {}
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        services_status["database"] = "healthy"
    except Exception as e:
        services_status["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        await redis_client.ping()
        services_status["redis"] = "healthy"
    except Exception as e:
        services_status["redis"] = f"unhealthy: {str(e)}"
    
    # Overall status
    all_healthy = all(v == "healthy" for v in services_status.values())
    
    return StandardResponse(
        success=all_healthy,
        data={
            "status": "ready" if all_healthy else "not_ready",
            "services": services_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.get("/live")
async def liveness_check():
    """
    Liveness probe for Kubernetes.
    """
    return StandardResponse(
        success=True,
        data={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
