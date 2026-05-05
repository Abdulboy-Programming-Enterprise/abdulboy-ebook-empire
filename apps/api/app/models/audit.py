"""
Audit Model
============
Audit logging for admin actions and system changes.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TimestampMixin


class AuditLog(BaseModel, TimestampMixin):
    """Audit log for tracking administrative actions."""
    
    __tablename__ = "audit_logs"
    
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_email = Column(String(255), nullable=True)
    
    action_type = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=True)  # user, book, payment, etc.
    target_id = Column(UUID(as_uuid=True), nullable=True)
    
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])
