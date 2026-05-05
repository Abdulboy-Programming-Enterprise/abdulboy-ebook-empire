"""
Webhook Routes
==============
Webhook endpoints for payment gateway callbacks.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.core.logger import logger
from app.packages.payments.stripe.webhooks import handle_stripe_webhook
from app.packages.payments.opay.webhooks import handle_opay_webhook
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Stripe webhook endpoint for payment events.
    """
    payload = await request.body()
    signature = request.headers.get('stripe-signature')
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    try:
        result = await handle_stripe_webhook(payload, signature, db)
        if result.get('success'):
            return StandardResponse(success=True, message="Webhook processed")
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Webhook processing failed'))
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opay")
async def opay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    OPay webhook endpoint for payment events.
    """
    payload = await request.body()
    signature = request.headers.get('opay-signature')
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    try:
        result = await handle_opay_webhook(payload, signature, db)
        if result.get('success'):
            return StandardResponse(success=True, message="Webhook processed")
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Webhook processing failed'))
    except Exception as e:
        logger.error(f"OPay webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/paypal")
async def paypal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    PayPal webhook endpoint (placeholder).
    """
    payload = await request.body()
    logger.info(f"PayPal webhook received: {len(payload)} bytes")
    # TODO: Implement PayPal webhook handling
    return StandardResponse(success=True, message="Webhook received")


@router.post("/flutterwave")
async def flutterwave_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Flutterwave webhook endpoint (placeholder).
    """
    payload = await request.body()
    logger.info(f"Flutterwave webhook received: {len(payload)} bytes")
    # TODO: Implement Flutterwave webhook handling
    return StandardResponse(success=True, message="Webhook received")
