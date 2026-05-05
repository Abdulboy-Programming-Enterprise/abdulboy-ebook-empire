"""
Affiliate Model
===============
Affiliate marketing tracking for referrals and commissions.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TimestampMixin


class AffiliateLink(BaseModel, TimestampMixin):
    """Affiliate link model for tracking referrals."""
    
    __tablename__ = "affiliate_links"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    code = Column(String(50), unique=True, nullable=False)
    commission_rate = Column(Float, default=0.10)  # 10% default
    clicks_count = Column(Integer, default=0)
    conversions_count = Column(Integer, default=0)
    earnings_total = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User")
    clicks = relationship("AffiliateClick", back_populates="affiliate_link")
    
    def __repr__(self):
        return f"<AffiliateLink {self.code}>"


class AffiliateClick(BaseModel, TimestampMixin):
    """Individual click on an affiliate link."""
    
    __tablename__ = "affiliate_clicks"
    
    affiliate_link_id = Column(UUID(as_uuid=True), ForeignKey("affiliate_links.id", ondelete="CASCADE"), nullable=False)
    
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    
    converted_at = Column(DateTime, nullable=True)
    conversion_amount = Column(Float, nullable=True)
    
    # Relationships
    affiliate_link = relationship("AffiliateLink", back_populates="clicks")
