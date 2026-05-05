"""
Error Handler Middleware
========================
Global exception handling and standardized error responses.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from datetime import datetime
from typing import Union
from app.core.logger import logger
from app.core.exceptions import AppException
from app.schemas.response import ErrorResponse
from app.core.config import settings


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle exceptions and return standardized error responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        
        except StarletteHTTPException as e:
            return self._handle_http_exception(e, request)
        
        except AppException as e:
            return self._handle_app_exception(e, request)
        
        except HTTPException as e:
            return self._handle_http_exception(e, request)
        
        except Exception as e:
            return self._handle_unexpected_exception(e, request)
    
    def _handle_http_exception(self, exc: StarletteHTTPException, request: Request) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.warning(
            f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url.path}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                message=str(exc.detail),
                status_code=exc.status_code,
            ).model_dump(),
        )
    
    def _handle_app_exception(self, exc: AppException, request: Request) -> JSONResponse:
        """Handle custom application exceptions."""
        logger.error(
            f"App exception: {exc.message} - {request.method} {request.url.path}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                message=exc.message,
                errors=[exc.details] if exc.details else None,
                status_code=exc.status_code,
            ).model_dump(),
        )
    
    def _handle_unexpected_exception(self, exc: Exception, request: Request) -> JSONResponse:
        """Handle unexpected exceptions."""
        error_id = datetime.utcnow().timestamp()
        
        # Log full traceback
        logger.error(
            f"Unhandled exception [{error_id}]: {str(exc)}\n{traceback.format_exc()}"
        )
        
        message = "An unexpected error occurred"
        if settings.APP_DEBUG:
            message = f"{str(exc)}"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=message,
                errors=[{"error_id": str(error_id)}] if not settings.APP_DEBUG else None,
                status_code=500,
            ).model_dump(),
        )
