"""
Middleware Package
==================
FastAPI middleware components for request/response processing.
"""

from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.cors import CORSMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.audit_log import AuditLogMiddleware
from app.middleware.compression import CompressionMiddleware

__all__ = [
    "AuthMiddleware",
    "RateLimitMiddleware",
    "ErrorHandlerMiddleware",
    "CORSMiddleware",
    "RequestIDMiddleware",
    "AuditLogMiddleware",
    "CompressionMiddleware",
]
