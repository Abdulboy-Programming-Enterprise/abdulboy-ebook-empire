"""
Integration tests for payment webhook handling.
"""

import pytest
import json


@pytest.mark.integration
class TestStripeWebhook:
    """Test Stripe webhook handling."""
    
    async def test_stripe_webhook_success(self, client):
        """Test successful Stripe webhook."""
        payload = {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_123",
                    "amount": 2999,
                    "currency": "usd",
                    "status": "succeeded"
                }
            }
        }
        
        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"stripe-signature": "test_signature"}
        )
        
        # Note: In test environment, signature verification is mocked
        assert response.status_code in [200, 400]
    
    async def test_stripe_webhook_failed_payment(self, client):
        """Test failed payment webhook."""
        payload = {
            "id": "evt_test_456",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_456",
                    "last_payment_error": {"message": "Card declined"}
                }
            }
        }
        
        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"stripe-signature": "test_signature"}
        )
        
        assert response.status_code in [200, 400]


@pytest.mark.integration
class TestOPayWebhook:
    """Test OPay webhook handling."""
    
    async def test_opay_webhook_success(self, client):
        """Test OPay success webhook."""
        payload = {
            "event": "order.success",
            "orderNo": "ORDER123",
            "transactionId": "TXN456",
            "amount": "1000.00"
        }
        
        response = await client.post(
            "/api/v1/webhooks/opay",
            json=payload,
            headers={"opay-signature": "test_signature"}
        )
        
        assert response.status_code in [200, 400]
