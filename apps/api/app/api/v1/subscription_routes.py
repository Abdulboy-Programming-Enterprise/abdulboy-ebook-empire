"""
Subscription Routes
===================
Subscription plan management and user subscription endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_db
from app.models.user import User, SubscriptionStatus
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.schemas.response import StandardResponse
from app.api.deps import get_current_user, get_current_admin_user
from app.core.logger import logger

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/plans", response_model=StandardResponse)
async def get_subscription_plans(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available subscription plans.
    """
    result = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True)
        .order_by(SubscriptionPlan.sort_order)
    )
    plans = result.scalars().all()
    
    plan_responses = []
    for plan in plans:
        plan_responses.append({
            "id": str(plan.id),
            "name": plan.name,
            "slug": plan.slug,
            "description": plan.description,
            "price": plan.price,
            "currency": plan.currency,
            "duration_days": plan.duration_days,
            "features": plan.features.split(',') if plan.features else [],
            "books_per_month": plan.books_per_month,
            "download_limit": plan.download_limit,
            "is_popular": plan.name == "Premium",
        })
    
    return StandardResponse(success=True, data=plan_responses)


@router.get("/my-subscription", response_model=StandardResponse)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's subscription details.
    """
    # Get active subscription
    result = await db.execute(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == current_user.id,
            UserSubscription.status == "active"
        )
        .order_by(UserSubscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()
    
    subscription_data = {
        "status": current_user.subscription_status.value,
        "is_active": current_user.has_active_subscription,
    }
    
    if subscription:
        # Get plan details
        plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        
        subscription_data.update({
            "plan_name": plan.name if plan else None,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "days_remaining": (subscription.end_date - datetime.utcnow()).days if subscription.end_date > datetime.utcnow() else 0,
            "auto_renew": subscription.auto_renew,
        })
    
    return StandardResponse(success=True, data=subscription_data)


@router.post("/subscribe/{plan_id}")
async def subscribe_to_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Subscribe to a subscription plan (creates payment intent).
    """
    # Get plan
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if already subscribed
    if current_user.has_active_subscription:
        raise HTTPException(status_code=400, detail="Already have an active subscription")
    
    # Create payment intent (redirect to payment)
    from app.api.v1.payment_routes import create_payment_intent
    from app.schemas.payment import PaymentCreate
    
    payment_data = PaymentCreate(
        amount=plan.price,
        currency=plan.currency,
        payment_method="stripe",
        item_type="subscription",
        item_id=plan_id,
        success_url=None,
        cancel_url=None,
    )
    
    # This would create a payment intent and return redirect URL
    # For now, return plan info
    return StandardResponse(
        success=True,
        message="Proceed to payment",
        data={
            "plan": {
                "id": str(plan.id),
                "name": plan.name,
                "price": plan.price,
                "currency": plan.currency,
            },
            "payment_url": f"/api/v1/payments/create-intent",
        }
    )


@router.post("/cancel")
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel current subscription (effective at end of period).
    """
    # Find active subscription
    result = await db.execute(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == current_user.id,
            UserSubscription.status == "active"
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    # Cancel at period end
    subscription.auto_renew = False
    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.utcnow()
    await db.commit()
    
    # Update user status (will expire at end_date)
    current_user.subscription_status = SubscriptionStatus.CANCELLED
    await db.commit()
    
    logger.info(f"User {current_user.email} cancelled subscription")
    
    return StandardResponse(
        success=True,
        message=f"Subscription cancelled. Access continues until {subscription.end_date.date()}"
    )
