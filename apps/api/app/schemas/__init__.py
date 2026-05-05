"""
Schemas Package
================
Pydantic schemas for request/response validation.
"""

from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin, Token, TokenRefresh
from app.schemas.book import BookCreate, BookUpdate, BookResponse, BookListResponse, BookSearchParams
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentWebhook
from app.schemas.response import StandardResponse, PaginatedResponse, ErrorResponse
from app.schemas.badge import BadgeResponse, UserBadgeResponse, BadgeCriteria
from app.schemas.gamification import LeaderboardEntry, PointsTransaction, ChallengeResponse

__all__ = [
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenRefresh",
    "BookCreate",
    "BookUpdate",
    "BookResponse",
    "BookListResponse",
    "BookSearchParams",
    "PaymentCreate",
    "PaymentResponse",
    "PaymentWebhook",
    "StandardResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "BadgeResponse",
    "UserBadgeResponse",
    "BadgeCriteria",
    "LeaderboardEntry",
    "PointsTransaction",
    "ChallengeResponse",
]
