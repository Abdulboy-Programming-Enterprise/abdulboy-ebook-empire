"""
Payment Repository
==================
Database operations for payments.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    """Repository for payment database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID."""
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get payment by gateway transaction ID."""
        result = await self.db.execute(select(Payment).where(Payment.gateway_transaction_id == transaction_id))
        return result.scalar_one_or_none()
    
    async def create(self, payment_data: dict) -> Payment:
        """Create a new payment record."""
        payment = Payment(**payment_data)
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment
    
    async def update_status(
        self,
        payment_id: str,
        status: PaymentStatus,
        gateway_response: str = None,
        error_message: str = None
    ) -> Optional[Payment]:
        """Update payment status."""
        payment = await self.get_by_id(payment_id)
        if not payment:
            return None
        
        payment.status = status
        if gateway_response:
            payment.gateway_response = gateway_response
        if error_message:
            payment.error_message = error_message
        
        if status == PaymentStatus.COMPLETED:
            from datetime import datetime
            payment.paid_at = datetime.utcnow()
        elif status == PaymentStatus.REFUNDED:
            from datetime import datetime
            payment.refunded_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(payment)
        return payment
    
    async def list_user_payments(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Payment], int]:
        """List payments for a user."""
        query = select(Payment).where(Payment.user_id == user_id)
        
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.order_by(Payment.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        payments = result.scalars().all()
        
        return payments, total or 0
