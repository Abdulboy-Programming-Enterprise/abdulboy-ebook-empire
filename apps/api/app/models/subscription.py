"""
Subscription Model
==================
Subscription plans and user subscription models.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TimestampMixin


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class SubscriptionPlan(BaseModel, TimestampMixin):
    """Subscription plan model."""
    
    __tablename__ = "subscription_plans"
    
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    duration_days = Column(Integer, nullable=False)
    
    # Features as JSON
    features = Column(Text, nullable=True)  # JSON string
    
    # Limits
    books_per_month = Column(Integer, nullable=True)
    download_limit = Column(Integer, nullable=True)
    
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # Relationships
    user_subscriptions = relationship("UserSubscription", back_populates="plan")
    
    def __repr__(self):
        return f"<SubscriptionPlan {self.name}>"


class UserSubscription(BaseModel, TimestampMixin):
    """User subscription record."""
    
    __tablename__ = "user_subscriptions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    auto_renew = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    
    status = Column(String(20), default=SubscriptionStatus.ACTIVE)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="user_subscriptions")
    payment = relationship("Payment", foreign_keys=[payment_id])
    
    @property
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE and self.end_date > datetime.utcnow()
    
    def __repr__(self):
        return f"<UserSubscription user={self.user_id} plan={self.plan_id}>"
