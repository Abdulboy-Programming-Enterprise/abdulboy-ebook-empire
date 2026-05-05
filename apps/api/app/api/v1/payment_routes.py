"""
Payment Routes
==============
Payment processing endpoints for Stripe, OPay, and other gateways.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional
import stripe
from app.core.database import get_db
from app.models.user import User
from app.models.payment import Payment, PaymentStatus, PaymentMethod, PaymentItemType
from app.models.book import Book
from app.models.subscription import SubscriptionPlan
from app.models.booking import Booking
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentIntentResponse, PaymentVerification
from app.schemas.response import StandardResponse
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logger import logger
from app.packages.payments.payment_orchestrator import get_payment_orchestrator
from app.tasks.email_jobs import send_purchase_confirmation

router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/create-intent", response_model=StandardResponse[PaymentIntentResponse])
async def create_payment_intent(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a payment intent for a book, subscription, or custom booking.
    """
    # Validate item exists
    item = None
    if payment_data.item_type == PaymentItemType.BOOK.value:
        result = await db.execute(select(Book).where(Book.id == payment_data.item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Check if user already owns this book
        from app.models.payment import UserBookPurchase
        purchase_result = await db.execute(
            select(UserBookPurchase).where(
                UserBookPurchase.user_id == current_user.id,
                UserBookPurchase.book_id == payment_data.item_id
            )
        )
        if purchase_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="You already own this book")
    
    elif payment_data.item_type == PaymentItemType.SUBSCRIPTION.value:
        result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == payment_data.item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    elif payment_data.item_type == PaymentItemType.CUSTOM_BOOKING.value:
        result = await db.execute(select(Booking).where(Booking.id == payment_data.item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Booking not found")
    
    # Create payment record
    payment = Payment(
        user_id=current_user.id,
        amount=payment_data.amount,
        currency=payment_data.currency,
        payment_method=payment_data.payment_method,
        item_type=payment_data.item_type,
        item_id=payment_data.item_id,
        status=PaymentStatus.PENDING,
        metadata=str(payment_data.metadata) if payment_data.metadata else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    # Initialize payment orchestrator
    orchestrator_config = {
        'stripe': {
            'enabled': True,
            'secret_key': settings.STRIPE_SECRET_KEY,
            'publishable_key': settings.STRIPE_PUBLIC_KEY,
            'webhook_secret': settings.STRIPE_WEBHOOK_SECRET,
        },
        'opay': {
            'enabled': True,
            'merchant_id': settings.OPAY_MERCHANT_ID,
            'public_key': settings.OPAY_PUBLIC_KEY,
            'secret_key': settings.OPAY_SECRET_KEY,
            'api_url': 'https://sandboxapi.opaycheckout.com' if settings.OPAY_ENV == 'sandbox' else 'https://api.opaycheckout.com',
        }
    }
    
    orchestrator = get_payment_orchestrator(orchestrator_config)
    
    # Create payment with provider
    from app.packages.payments.payment_orchestrator import PaymentProvider
    provider = PaymentProvider.STRIPE if payment_data.payment_method == 'stripe' else PaymentProvider.OPAY
    
    result = orchestrator.create_payment(
        provider=provider,
        amount=payment_data.amount,
        currency=payment_data.currency,
        metadata={
            'payment_id': str(payment.id),
            'user_id': str(current_user.id),
            'item_type': payment_data.item_type,
            'item_id': payment_data.item_id,
            'item_name': item.title if hasattr(item, 'title') else item.name if hasattr(item, 'name') else 'Purchase',
        },
        customer_email=current_user.email,
        return_url=payment_data.success_url or f"https://abdulboy-ebook.com/payment-success?payment_id={payment.id}"
    )
    
    if not result.success:
        payment.status = PaymentStatus.FAILED
        payment.error_message = result.message
        await db.commit()
        raise HTTPException(status_code=400, detail=result.message)
    
    # Update payment with gateway info
    payment.gateway_transaction_id = result.transaction_id
    payment.gateway_reference = result.reference
    await db.commit()
    
    return StandardResponse(
        success=True,
        data=PaymentIntentResponse(
            payment_id=str(payment.id),
            client_secret=result.data.get('client_secret') if result.data else None,
            checkout_url=result.data.get('checkout_url') if result.data else None,
            order_no=result.data.get('order_no') if result.data else None,
            redirect_url=result.data.get('approval_url') or result.data.get('checkout_url'),
        )
    )


@router.post("/verify", response_model=StandardResponse)
async def verify_payment(
    verification: PaymentVerification,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verify payment status after redirect from payment gateway.
    """
    # Find payment
    result = await db.execute(select(Payment).where(Payment.id == verification.payment_id))
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if payment.status == PaymentStatus.COMPLETED:
        return StandardResponse(
            success=True,
            message="Payment already completed",
            data={"status": "completed"}
        )
    
    # Initialize orchestrator
    orchestrator_config = {
        'stripe': {
            'enabled': True,
            'secret_key': settings.STRIPE_SECRET_KEY,
        },
        'opay': {
            'enabled': True,
            'merchant_id': settings.OPAY_MERCHANT_ID,
            'secret_key': settings.OPAY_SECRET_KEY,
            'api_url': 'https://sandboxapi.opaycheckout.com' if settings.OPAY_ENV == 'sandbox' else 'https://api.opaycheckout.com',
        }
    }
    
    orchestrator = get_payment_orchestrator(orchestrator_config)
    
    from app.packages.payments.payment_orchestrator import PaymentProvider
    provider = PaymentProvider.STRIPE if payment.payment_method == 'stripe' else PaymentProvider.OPAY
    
    # Verify payment
    verify_result = orchestrator.verify_payment(
        provider=provider,
        reference=verification.reference or payment.gateway_reference,
        transaction_id=verification.transaction_id or payment.gateway_transaction_id
    )
    
    if verify_result.success and verify_result.status.value == 'completed':
        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = datetime.utcnow()
        await db.commit()
        
        # Send confirmation email
        user_result = await db.execute(select(User).where(User.id == payment.user_id))
        user = user_result.scalar_one()
        
        send_purchase_confirmation.delay(
            user_email=user.email,
            user_name=user.full_name,
            order_id=str(payment.id),
            items=[{
                'id': str(payment.item_id),
                'type': payment.item_type,
                'amount': payment.amount,
            }],
            total_amount=payment.amount,
            payment_method=payment.payment_method
        )
        
        return StandardResponse(
            success=True,
            message="Payment verified successfully",
            data={"status": "completed"}
        )
    elif verify_result.status.value == 'pending':
        return StandardResponse(
            success=True,
            message="Payment pending",
            data={"status": "pending"}
        )
    else:
        payment.status = PaymentStatus.FAILED
        payment.error_message = verify_result.message
        await db.commit()
        
        return StandardResponse(
            success=False,
            message=f"Payment failed: {verify_result.message}",
            data={"status": "failed"}
        )


@router.get("/history", response_model=StandardResponse)
async def get_payment_history(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's payment history.
    """
    query = select(Payment).where(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc())
    
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    payments = result.scalars().all()
    
    total_result = await db.execute(select(func.count()).select_from(Payment).where(Payment.user_id == current_user.id))
    total = total_result.scalar()
    
    payment_responses = []
    for payment in payments:
        payment_responses.append({
            "id": str(payment.id),
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "item_type": payment.item_type,
            "item_id": str(payment.item_id),
            "status": payment.status.value,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "created_at": payment.created_at.isoformat(),
        })
    
    return StandardResponse(
        success=True,
        data={
            "items": payment_responses,
            "total": total or 0,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total else 0,
        }
    )


@router.get("/{payment_id}", response_model=StandardResponse)
async def get_payment_details(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed payment information.
    """
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return StandardResponse(
        success=True,
        data={
            "id": str(payment.id),
            "user_id": str(payment.user_id),
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "item_type": payment.item_type,
            "item_id": str(payment.item_id),
            "status": payment.status.value,
            "gateway_transaction_id": payment.gateway_transaction_id,
            "gateway_reference": payment.gateway_reference,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "created_at": payment.created_at.isoformat(),
        }
    )
