"""
Integration tests for database operations.
"""

import pytest
from sqlalchemy import select, text

from app.models.user import User
from app.models.book import Book


@pytest.mark.integration
class TestDatabaseConnection:
    """Test database connectivity."""
    
    async def test_db_connection(self, db_session):
        """Test database connection is active."""
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    async def test_create_and_query_user(self, db_session):
        """Test user creation and query."""
        user = User(
            email="db_test@example.com",
            password_hash="hash",
            full_name="DB Test User"
        )
        db_session.add(user)
        await db_session.commit()
        
        result = await db_session.execute(
            select(User).where(User.email == "db_test@example.com")
        )
        found = result.scalar_one()
        
        assert found.id == user.id
        assert found.full_name == "DB Test User"


@pytest.mark.integration
class TestDatabaseRelationships:
    """Test database relationships."""
    
    async def test_user_book_relationship(self, db_session, test_user, test_book):
        """Test user-book purchase relationship."""
        from app.models.payment import UserBookPurchase
        
        purchase = UserBookPurchase(
            user_id=test_user.id,
            book_id=test_book.id
        )
        db_session.add(purchase)
        await db_session.commit()
        
        # Query user's purchased books
        result = await db_session.execute(
            select(Book).join(UserBookPurchase).where(UserBookPurchase.user_id == test_user.id)
        )
        purchased_books = result.scalars().all()
        
        assert len(purchased_books) >= 1
        assert purchased_books[0].id == test_book.id
