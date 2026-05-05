"""
Subscription Service
====================
Business logic for subscription management.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.models.user import User, SubscriptionStatus


class SubscriptionService:
    """Service for subscription operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_plans(self) -> List[SubscriptionPlan]:
        """Get all active subscription plans."""
        result = await self.db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active == True)
            .order_by(SubscriptionPlan.sort_order)
        )
        return result.scalars().all()
    
    async def get_plan_by_id(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get subscription plan by ID."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        return result.scalar_one_or_none()
    
    async def subscribe_user(self, user_id: str, plan_id: str, payment_id: str) -> Optional[UserSubscription]:
        """Subscribe a user to a plan."""
        plan = await self.get_plan_by_id(plan_id)
        if not plan:
            return None
        
        # Deactivate existing subscriptions
        await self.db.execute(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "active"
            )
        )
        
        # Create new subscription
        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            payment_id=payment_id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
            auto_renew=True,
            status="active",
        )
        
        self.db.add(subscription)
        
        # Update user subscription status
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        
        status_map = {
            "Basic": SubscriptionStatus.BASIC,
            "Premium": SubscriptionStatus.PREMIUM,
        }
        user.subscription_status = status_map.get(plan.name, SubscriptionStatus.BASIC)
        user.subscription_started_at = datetime.utcnow()
        user.subscription_ends_at = datetime.utcnow() + timedelta(days=plan.duration_days)
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        return subscription
    
    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel user's active subscription."""
        result = await self.db.execute(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "active"
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return False
        
        subscription.auto_renew = False
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        
        # Update user status
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        user.subscription_status = SubscriptionStatus.CANCELLED
        
        await self.db.commit()
        
        return True
    
    async def check_expiring_subscriptions(self) -> List[UserSubscription]:
        """Find subscriptions expiring in the next 7 days."""
        cutoff = datetime.utcnow() + timedelta(days=7)
        
        result = await self.db.execute(
            select(UserSubscription)
            .where(
                UserSubscription.status == "active",
                UserSubscription.end_date <= cutoff,
                UserSubscription.end_date > datetime.utcnow()
            )
        )
        return result.scalars().all()
