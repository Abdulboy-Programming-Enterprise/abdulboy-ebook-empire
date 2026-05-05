"""
Payment Model
=============
Payment transactions and user purchase records.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TimestampMixin


class PaymentMethod(str, enum.Enum):
    STRIPE = "stripe"
    OPAY = "opay"
    PAYPAL = "paypal"
    FLUTTERWAVE = "flutterwave"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentItemType(str, enum.Enum):
    BOOK = "book"
    SUBSCRIPTION = "subscription"
    CUSTOM_BOOKING = "custom_booking"


class Payment(BaseModel, TimestampMixin):
    """Payment transaction model."""
    
    __tablename__ = "payments"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50), nullable=False)
    
    # Item purchased
    item_type = Column(String(20), nullable=False)
    item_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Gateway information
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_reference = Column(String(255), nullable=True)
    gateway_response = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default=PaymentStatus.PENDING)
    
    # Metadata
    metadata = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    paid_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    book_purchase = relationship("UserBookPurchase", back_populates="payment", uselist=False)
    
    def __repr__(self):
        return f"<Payment {self.id} - {self.amount} {self.currency}>"


class UserBookPurchase(BaseModel):
    """User book purchase record (library)."""
    
    __tablename__ = "user_book_purchases"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    
    purchase_price = Column(Float, nullable=True)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    
    # Access tracking
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="books_purchased")
    book = relationship("Book", back_populates="purchases")
    payment = relationship("Payment", back_populates="book_purchase")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='uq_user_book'),
    )
