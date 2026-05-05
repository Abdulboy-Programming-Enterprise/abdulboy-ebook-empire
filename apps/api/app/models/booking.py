"""
Booking Model
=============
Custom book booking requests from users.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TimestampMixin


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELIVERED = "delivered"


class Booking(BaseModel, TimestampMixin):
    """Custom book booking model."""
    
    __tablename__ = "bookings"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    
    # Booking details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    genre = Column(String(100), nullable=True)
    word_count = Column(Integer, nullable=True)
    
    # Requirements
    deadline = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=True)
    requirements = Column(Text, nullable=True)
    attachments = Column(Text, nullable=True)  # JSON array of URLs
    
    # Status
    status = Column(String(20), default=BookingStatus.PENDING)
    
    # Communication
    admin_notes = Column(Text, nullable=True)
    user_notes = Column(Text, nullable=True)
    
    # Delivery
    delivery_url = Column(String(500), nullable=True)
    
    # Timestamps
    delivered_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    payment = relationship("Payment", foreign_keys=[payment_id])
    
    def __repr__(self):
        return f"<Booking {self.id} - {self.title}>"
