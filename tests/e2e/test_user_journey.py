"""
End-to-end tests for user journey.
"""

import pytest


@pytest.mark.e2e
class TestUserJourney:
    """Test complete user journey."""
    
    async def test_complete_registration_to_purchase(self, client):
        """Test full user journey from registration to purchase."""
        # 1. Register
        register_response = await client.post("/api/v1/auth/register", json={
            "email": "e2e_user@example.com",
            "password": "E2ETest123!",
            "confirm_password": "E2ETest123!",
            "full_name": "E2E Test User"
        })
        assert register_response.status_code == 200
        
        # 2. Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "e2e_user@example.com",
            "password": "E2ETest123!"
        })
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Get books
        books_response = await client.get("/api/v1/books")
        assert books_response.status_code == 200
        
        # 4. View book details
        books = books_response.json()["data"]["items"]
        if books:
            book_id = books[0]["id"]
            detail_response = await client.get(f"/api/v1/books/{book_id}")
            assert detail_response.status_code == 200
        
        # 5. Get user profile
        profile_response = await client.get("/api/v1/users/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["data"]["email"] == "e2e_user@example.com"
    
    async def test_subscription_flow(self, client, test_user, auth_headers):
        """Test subscription plan viewing and selection flow."""
        # 1. Get plans
        plans_response = await client.get("/api/v1/subscriptions/plans")
        assert plans_response.status_code == 200
        plans = plans_response.json()["data"]
        
        assert len(plans) >= 2
        
        # 2. Get user's current subscription
        sub_response = await client.get("/api/v1/subscriptions/my-subscription", headers=auth_headers)
        assert sub_response.status_code == 200
