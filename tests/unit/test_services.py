"""
Unit tests for core services.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.users.service import UserManagementService
from app.services.books.service import BookManagementService


@pytest.mark.unit
class TestUserService:
    """Test user management service."""
    
    @pytest.fixture
    def user_service(self, db_session):
        """Create user service instance."""
        return UserManagementService(db_session)
    
    async def test_create_user(self, user_service):
        """Test creating a user via service."""
        user = await user_service.create_user(
            email="service@test.com",
            password="TestPass123!",
            full_name="Service Test User"
        )
        
        assert user is not None
        assert user.email == "service@test.com"
        assert user.full_name == "Service Test User"
    
    async def test_get_user_by_email(self, user_service, test_user):
        """Test retrieving user by email."""
        found = await user_service.get_user_by_email(test_user.email)
        
        assert found is not None
        assert found.id == test_user.id
    
    async def test_update_user(self, user_service, test_user):
        """Test updating user information."""
        updated = await user_service.update_user(
            str(test_user.id),
            {"full_name": "Updated Name"}
        )
        
        assert updated is not None
        assert updated.full_name == "Updated Name"


@pytest.mark.unit
class TestBookService:
    """Test book management service."""
    
    @pytest.fixture
    def book_service(self, db_session):
        """Create book service instance."""
        return BookManagementService(db_session)
    
    async def test_create_book(self, book_service):
        """Test creating a book via service."""
        book_data = {
            "title": "Service Test Book",
            "author_name": "Service Author",
            "total_pages": 150,
            "preview_pages": 15,
            "price": 14.99
        }
        result = await book_service.create_book(book_data)
        
        assert result is not None
        assert result["title"] == "Service Test Book"
    
    async def test_list_books(self, book_service, test_book):
        """Test listing books."""
        books, total = await book_service.list_books(limit=10)
        
        assert total >= 1
        assert len(books) >= 1
