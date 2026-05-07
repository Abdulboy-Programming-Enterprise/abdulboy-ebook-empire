"""
Unit tests for payment processing.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.payments.payment_service import PaymentService
from app.models.payment import PaymentStatus


@pytest.mark.unit
class TestPaymentService:
    """Test payment service functionality."""
    
    @pytest.fixture
    def payment_service(self, db_session):
        """Create payment service instance."""
        return PaymentService(db_session)
    
    async def test_create_payment(self, payment_service, test_user):
        """Test creating a payment record."""
        payment_data = {
            "user_id": test_user.id,
            "amount": 29.99,
            "currency": "USD",
            "payment_method": "stripe",
            "item_type": "book",
            "item_id": "book-123"
        }
        result = await payment_service.create_payment(payment_data)
        
        assert result is not None
        assert result["amount"] == 29.99
        assert "id" in result
    
    async def test_complete_payment(self, payment_service, test_user):
        """Test completing a payment."""
        # Create payment first
        payment_data = {
            "user_id": test_user.id,
            "amount": 29.99,
            "currency": "USD",
            "payment_method": "stripe",
            "item_type": "book",
            "item_id": "book-123"
        }
        payment = await payment_service.create_payment(payment_data)
        
        # Complete payment
        result = await payment_service.complete_payment(payment["id"], "txn_123")
        
        assert result is not None
        assert result["status"] == "completed"
    
    async def test_fail_payment(self, payment_service, test_user):
        """Test failing a payment."""
        payment_data = {
            "user_id": test_user.id,
            "amount": 29.99,
            "currency": "USD",
            "payment_method": "stripe",
            "item_type": "book",
            "item_id": "book-123"
        }
        payment = await payment_service.create_payment(payment_data)
        
        result = await payment_service.fail_payment(payment["id"], "Card declined")
        
        assert result is not None
        assert result["status"] == "failed"
        assert "error_message" in result
