"""
Payment Management Service
==========================
High-level service for payment management with gateway integration.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.payments.repository import PaymentRepository
from services.payments.payment import PaymentService
from app.models.payment import Payment
from app.core.config import settings
from app.core.logger import logger


class PaymentManagementService:
    """High-level service for payment management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaymentRepository(db)
        self.payment_service = PaymentService(self.repository)
    
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID."""
        return await self.repository.get_by_id(payment_id)
    
    async def create_payment(self, payment_data: dict) -> dict:
        """Create a new payment."""
        return await self.payment_service.create_payment(payment_data)
    
    async def process_successful_payment(self, payment_id: str, gateway_response: str) -> Optional[dict]:
        """Process successful payment."""
        result = await self.payment_service.complete_payment(payment_id, gateway_response)
        
        if result:
            # Grant access to purchased item
            payment = await self.repository.get_by_id(payment_id)
            if payment:
                await self._grant_access(payment)
        
        return result
    
    async def _grant_access(self, payment: Payment) -> None:
        """Grant access to purchased item."""
        try:
            if payment.item_type == "book":
                from app.models.payment import UserBookPurchase
                purchase = UserBookPurchase(
                    user_id=payment.user_id,
                    book_id=payment.item_id,
                    payment_id=payment.id,
                )
                self.db.add(purchase)
                await self.db.commit()
                logger.info(f"Granted book access for user {payment.user_id} to book {payment.item_id}")
            
            elif payment.item_type == "subscription":
                from app.models.user import SubscriptionStatus
                from datetime import datetime, timedelta
                
                user_result = await self.db.execute(
                    select(User).where(User.id == payment.user_id)
                )
                user = user_result.scalar_one()
                
                user.subscription_status = SubscriptionStatus.PREMIUM
                user.subscription_started_at = datetime.utcnow()
                user.subscription_ends_at = datetime.utcnow() + timedelta(days=30)
                await self.db.commit()
                logger.info(f"Activated subscription for user {payment.user_id}")
                
        except Exception as e:
            logger.error(f"Failed to grant access: {e}")
