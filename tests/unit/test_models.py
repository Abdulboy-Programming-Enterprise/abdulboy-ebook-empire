"""
Unit tests for database models.
"""

import pytest
from datetime import datetime
from sqlalchemy import select

from app.models.user import User, AccountType, SubscriptionStatus
from app.models.book import Book, BookStatus
from app.models.payment import Payment, PaymentStatus


@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""
    
    async def test_create_user(self, db_session):
        """Test creating a new user."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            account_type=AccountType.NORMAL,
            subscription_status=SubscriptionStatus.FREE
        )
        db_session.add(user)
        await db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.account_type == AccountType.NORMAL
        assert user.created_at is not None
    
    async def test_user_properties(self, db_session):
        """Test user property methods."""
        user = User(
            email="admin@test.com",
            password_hash="hash",
            full_name="Admin User",
            account_type=AccountType.ADMIN
        )
        db_session.add(user)
        await db_session.commit()
        
        assert user.is_admin is True
        assert user.is_special is False
    
    async def test_user_soft_delete(self, db_session):
        """Test soft delete functionality."""
        user = User(
            email="delete@test.com",
            password_hash="hash",
            full_name="To Delete",
            account_type=AccountType.NORMAL
        )
        db_session.add(user)
        await db_session.commit()
        
        user.deleted_at = datetime.utcnow()
        await db_session.commit()
        
        result = await db_session.execute(select(User).where(User.email == "delete@test.com"))
        deleted_user = result.scalar_one_or_none()
        assert deleted_user.deleted_at is not None


@pytest.mark.unit
class TestBookModel:
    """Test Book model functionality."""
    
    async def test_create_book(self, db_session):
        """Test creating a new book."""
        book = Book(
            title="Test Book",
            slug="test-book",
            author_name="Test Author",
            total_pages=100,
            preview_pages=10,
            price=19.99,
            status=BookStatus.DRAFT
        )
        db_session.add(book)
        await db_session.commit()
        
        assert book.id is not None
        assert book.title == "Test Book"
        assert book.slug == "test-book"
        assert book.status == BookStatus.DRAFT
    
    async def test_publish_book(self, db_session):
        """Test publishing a book."""
        book = Book(
            title="To Publish",
            slug="to-publish",
            author_name="Test Author",
            total_pages=200,
            preview_pages=20,
            status=BookStatus.DRAFT
        )
        db_session.add(book)
        await db_session.commit()
        
        book.status = BookStatus.PUBLISHED
        book.published_at = datetime.utcnow()
        await db_session.commit()
        
        assert book.is_published is True
        assert book.published_at is not None


@pytest.mark.unit
class TestPaymentModel:
    """Test Payment model functionality."""
    
    async def test_create_payment(self, db_session, test_user):
        """Test creating a payment record."""
        payment = Payment(
            user_id=test_user.id,
            amount=29.99,
            currency="USD",
            payment_method="stripe",
            item_type="book",
            item_id="book-123",
            status=PaymentStatus.PENDING
        )
        db_session.add(payment)
        await db_session.commit()
        
        assert payment.id is not None
        assert payment.amount == 29.99
        assert payment.status == PaymentStatus.PENDING
