"""
Models Package
==============
SQLAlchemy ORM models for the database.
"""

from app.models.base import Base, TimestampMixin
from app.models.user import User
from app.models.book import Book, Tag, BookTag
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.models.booking import Booking
from app.models.payment import Payment, UserBookPurchase
from app.models.analytics import AnalyticsEvent
from app.models.suggestion import SuggestionLog
from app.models.affiliate import AffiliateLink, AffiliateClick
from app.models.notification import Notification
from app.models.audit import AuditLog
from app.models.badge import Badge, UserBadge
from app.models.achievement import Achievement, UserAchievement

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Book",
    "Tag",
    "BookTag",
    "SubscriptionPlan",
    "UserSubscription",
    "Booking",
    "Payment",
    "UserBookPurchase",
    "AnalyticsEvent",
    "SuggestionLog",
    "AffiliateLink",
    "AffiliateClick",
    "Notification",
    "AuditLog",
    "Badge",
    "UserBadge",
    "Achievement",
    "UserAchievement",
]
