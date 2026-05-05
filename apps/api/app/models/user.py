"""
User Model
==========
User account model with authentication and profile information.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TimestampMixin


class AccountType(str, enum.Enum):
    ADMIN = "admin"
    SPECIAL = "special"
    NORMAL = "normal"


class SubscriptionStatus(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class User(BaseModel, TimestampMixin):
    """User account model."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    # Account type
    account_type = Column(Enum(AccountType), default=AccountType.NORMAL, nullable=False)
    
    # User preferences
    theme = Column(String(20), default="light")
    text_size = Column(Integer, default=100)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    
    # Gamification
    total_points = Column(Integer, default=0)
    reading_streak = Column(Integer, default=0)
    last_active_at = Column(DateTime, nullable=True)
    
    # Subscription
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.FREE)
    subscription_started_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)
    
    # Verification
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    books_purchased = relationship("UserBookPurchase", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    reading_activities = relationship("ReadingActivity", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def is_admin(self) -> bool:
        return self.account_type == AccountType.ADMIN
    
    @property
    def is_special(self) -> bool:
        return self.account_type == AccountType.SPECIAL
    
    @property
    def has_active_subscription(self) -> bool:
        return self.subscription_status in [SubscriptionStatus.BASIC, SubscriptionStatus.PREMIUM] and (
            self.subscription_ends_at is None or self.subscription_ends_at > datetime.utcnow()
        )
    
    def __repr__(self):
        return f"<User {self.email}>"
