"""
End-to-end tests for admin actions.
"""

import pytest


@pytest.mark.e2e
class TestAdminActions:
    """Test admin panel functionality."""
    
    async def test_admin_login_and_dashboard(self, client, admin_user):
        """Test admin login and dashboard access."""
        # 1. Admin login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "Admin@123456"
        })
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get dashboard stats
        stats_response = await client.get("/api/v1/admin/dashboard/stats", headers=headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()["data"]
        
        assert "users" in stats
        assert "books" in stats
        assert "revenue" in stats
    
    async def test_admin_book_management(self, client, admin_user, auth_headers_admin):
        """Test admin book management."""
        # 1. Create book
        create_response = await client.post("/api/v1/admin/books", json={
            "title": "Admin Created Book",
            "author_name": "Admin Author",
            "total_pages": 200,
            "preview_pages": 20,
            "price": 24.99
        }, headers=auth_headers_admin)
        assert create_response.status_code == 200
        book_id = create_response.json()["data"]["id"]
        
        # 2. Publish book
        publish_response = await client.post(
            f"/api/v1/admin/books/{book_id}/publish",
            headers=auth_headers_admin
        )
        assert publish_response.status_code == 200
        
        # 3. Verify book is published
        get_response = await client.get(f"/api/v1/books/{book_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["status"] == "published"
    
    async def test_admin_user_management(self, client, admin_user, auth_headers_admin):
        """Test admin user management."""
        # 1. List users
        users_response = await client.get("/api/v1/admin/users", headers=auth_headers_admin)
        assert users_response.status_code == 200
        
        # 2. Create special user
        special_response = await client.post("/api/v1/admin/users/special", json={
            "email": "special@test.com",
            "full_name": "Special User"
        }, headers=auth_headers_admin)
        assert special_response.status_code == 200
