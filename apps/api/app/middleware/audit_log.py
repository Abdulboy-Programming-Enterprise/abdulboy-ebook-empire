"""
Audit Log Middleware
====================
Logs all API requests and responses for auditing purposes.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime
import json
from app.core.logger import logger
from app.core.database import SessionLocal
from app.models.audit import AuditLog


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log API requests and responses for admin auditing.
    """
    
    # Paths to exclude from audit logging
    EXCLUDED_PATHS = [
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/health/live",
        "/api/v1/webhooks",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip audit for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Only log for API routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        start_time = datetime.utcnow()
        
        # Get request body for logging (limited size)
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                body = body_bytes.decode("utf-8")[:1000]  # Limit size
                # Reconstruct request body
                request._body = body_bytes
            except Exception as e:
                # Best-effort body capture for audit logging; never block request flow.
                logger.debug(f"Skipping request body audit capture due to parse/read error: {e}")
        
        response = await call_next(request)
        
        # Log asynchronously (fire and forget)
        await self._log_request(
            request=request,
            response=response,
            start_time=start_time,
            request_body=body,
        )
        
        return response
    
    async def _log_request(
        self,
        request: Request,
        response: Response,
        start_time: datetime,
        request_body: str = None,
    ):
        """Log request details to audit table."""
        try:
            # Only log for authenticated requests
            user_id = getattr(request.state, "user_id", None)
            if not user_id:
                return
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Create audit log entry (async)
            db = SessionLocal()
            try:
                audit = AuditLog(
                    admin_id=user_id,
                    admin_email=None,  # Would fetch from user service
                    action_type=request.method,
                    target_type=request.url.path.split("/")[-2] if request.url.path.split("/") else None,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    created_at=datetime.utcnow(),
                )
                db.add(audit)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to create audit log: {e}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
