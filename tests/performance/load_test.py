"""
Load testing with Locust.
"""

from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    """Simulated user for load testing."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login when user starts."""
        self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "LoadTest123!"
        })
    
    @task(3)
    def view_books(self):
        """View book listings."""
        self.client.get("/api/v1/books")
    
    @task(2)
    def search_books(self):
        """Search for books."""
        self.client.get("/api/v1/books/search?q=python")
    
    @task(2)
    def view_book_detail(self):
        """View specific book details."""
        self.client.get("/api/v1/books/sample-book-id")
    
    @task(1)
    def view_subscription_plans(self):
        """View subscription plans."""
        self.client.get("/api/v1/subscriptions/plans")
    
    @task(1)
    def get_user_profile(self):
        """Get user profile."""
        self.client.get("/api/v1/users/me")


class AdminUser(HttpUser):
    """Simulated admin user for load testing."""
    
    wait_time = between(2, 5)
    
    @task
    def view_dashboard(self):
        """View admin dashboard."""
        self.client.get("/api/v1/admin/dashboard/stats")
    
    @task
    def view_users(self):
        """View users list."""
        self.client.get("/api/v1/admin/users")
