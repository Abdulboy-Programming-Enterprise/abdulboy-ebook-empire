"""
Payment Service
===============
Business logic for payment processing.
"""

from typing import Optional
from services.payments.repository import PaymentRepository
from app.models.payment import PaymentStatus


class PaymentService:
    """Service for payment business logic."""
    
    def __init__(self, repository: PaymentRepository):
        self.repository = repository
    
    async def create_payment(self, payment_data: dict) -> dict:
        """Create a new payment record."""
        payment = await self.repository.create(payment_data)
        return {
            "id": str(payment.id),
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value,
            "created_at": payment.created_at.isoformat(),
        }
    
    async def complete_payment(self, payment_id: str, gateway_response: str) -> Optional[dict]:
        """Mark payment as completed."""
        payment = await self.repository.update_status(
            payment_id,
            PaymentStatus.COMPLETED,
            gateway_response=gateway_response
        )
        
        if not payment:
            return None
        
        return {
            "id": str(payment.id),
            "status": payment.status.value,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        }
    
    async def fail_payment(self, payment_id: str, error_message: str) -> Optional[dict]:
        """Mark payment as failed."""
        payment = await self.repository.update_status(
            payment_id,
            PaymentStatus.FAILED,
            error_message=error_message
        )
        
        if not payment:
            return None
        
        return {
            "id": str(payment.id),
            "status": payment.status.value,
            "error_message": payment.error_message,
        }
    
    async def refund_payment(self, payment_id: str) -> Optional[dict]:
        """Mark payment as refunded."""
        payment = await self.repository.update_status(payment_id, PaymentStatus.REFUNDED)
        
        if not payment:
            return None
        
        return {
            "id": str(payment.id),
            "status": payment.status.value,
            "refunded_at": payment.refunded_at.isoformat() if payment.refunded_at else None,
        }
