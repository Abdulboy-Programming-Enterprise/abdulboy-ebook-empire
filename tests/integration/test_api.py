"""
Integration tests for API endpoints.
"""

import pytest


@pytest.mark.integration
class TestAuthAPI:
    """Test authentication API endpoints."""
    
    async def test_register_user(self, client):
        """Test user registration endpoint."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
            "full_name": "New Test User"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    async def test_login_success(self, client, test_user):
        """Test successful login."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test123456!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
    
    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        
        assert response.status_code == 401
    
    async def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "email" in data["data"]


@pytest.mark.integration
class TestBooksAPI:
    """Test books API endpoints."""
    
    async def test_list_books(self, client):
        """Test listing books endpoint."""
        response = await client.get("/api/v1/books")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
    
    async def test_search_books(self, client):
        """Test searching books."""
        response = await client.get("/api/v1/books/search?q=python")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    async def test_get_book_detail(self, client, test_book):
        """Test getting book details."""
        response = await client.get(f"/api/v1/books/{test_book.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_book.id)


@pytest.mark.integration
class TestSubscriptionsAPI:
    """Test subscriptions API endpoints."""
    
    async def test_get_plans(self, client):
        """Test getting subscription plans."""
        response = await client.get("/api/v1/subscriptions/plans")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
