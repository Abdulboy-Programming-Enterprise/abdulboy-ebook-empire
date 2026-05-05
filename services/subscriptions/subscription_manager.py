"""
Subscription Manager
====================
High-level subscription management service.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from services.subscriptions.subscription import SubscriptionService
from app.models.subscription import SubscriptionPlan, UserSubscription


class SubscriptionManager:
    """Manager for subscription operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = SubscriptionService(db)
    
    async def get_available_plans(self) -> List[dict]:
        """Get available subscription plans formatted for API."""
        plans = await self.service.get_plans()
        
        return [{
            "id": str(p.id),
            "name": p.name,
            "slug": p.slug,
            "description": p.description,
            "price": p.price,
            "currency": p.currency,
            "duration_days": p.duration_days,
            "features": p.features.split(',') if p.features else [],
            "books_per_month": p.books_per_month,
            "download_limit": p.download_limit,
        } for p in plans]
    
    async def subscribe(self, user_id: str, plan_id: str, payment_id: str) -> Optional[dict]:
        """Subscribe a user to a plan."""
        subscription = await self.service.subscribe_user(user_id, plan_id, payment_id)
        
        if not subscription:
            return None
        
        return {
            "id": str(subscription.id),
            "user_id": str(subscription.user_id),
            "plan_id": str(subscription.plan_id),
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "auto_renew": subscription.auto_renew,
            "status": subscription.status,
        }
    
    async def cancel(self, user_id: str) -> bool:
        """Cancel user's subscription."""
        return await self.service.cancel_subscription(user_id)
    
    async def get_user_subscription(self, user_id: str) -> Optional[dict]:
        """Get user's active subscription."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "active"
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        return {
            "id": str(subscription.id),
            "plan_id": str(subscription.plan_id),
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "days_remaining": (subscription.end_date - datetime.utcnow()).days,
            "auto_renew": subscription.auto_renew,
        }
