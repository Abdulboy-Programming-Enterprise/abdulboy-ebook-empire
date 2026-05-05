"""
Payment Schemas
===============
Pydantic schemas for payment-related operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime


class PaymentCreate(BaseModel):
    """Schema for creating a payment."""
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    payment_method: str = Field(..., pattern="^(stripe|opay|paypal|flutterwave)$")
    item_type: str = Field(..., pattern="^(book|subscription|custom_booking)$")
    item_id: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: str
    user_id: str
    amount: float
    currency: str
    payment_method: str
    item_type: str
    item_id: str
    status: str
    gateway_transaction_id: Optional[str]
    gateway_reference: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent response."""
    client_secret: Optional[str]
    checkout_url: Optional[str]
    order_no: Optional[str]
    payment_id: str
    redirect_url: Optional[str]


class PaymentWebhook(BaseModel):
    """Schema for payment webhook payload."""
    event_type: str
    payment_id: Optional[str]
    transaction_id: Optional[str]
    reference: Optional[str]
    status: str
    data: Optional[Dict[str, Any]] = None


class PaymentVerification(BaseModel):
    """Schema for payment verification."""
    payment_id: str
    reference: Optional[str] = None
    transaction_id: Optional[str] = None
