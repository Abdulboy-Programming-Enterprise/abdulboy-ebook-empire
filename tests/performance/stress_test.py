"""
Stress testing with Locust - high concurrency.
"""

from locust import HttpUser, task, between, events


class StressTestUser(HttpUser):
    """Stress test user with minimal wait time."""
    
    wait_time = between(0.1, 0.5)
    
    @task(5)
    def rapid_book_views(self):
        """Rapid book listing requests."""
        self.client.get("/api/v1/books")
    
    @task(3)
    def rapid_search(self):
        """Rapid search requests."""
        self.client.get("/api/v1/books/search?q=test")
    
    @task(1)
    def heavy_payload(self):
        """Request with larger payload."""
        self.client.post("/api/v1/books/search", json={
            "filters": {
                "categories": ["fiction", "non-fiction", "programming", "self-help"],
                "price_range": {"min": 0, "max": 50},
                "sort": "popular"
            }
        })


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called before test starts."""
    print("Starting stress test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called after test ends."""
    print("Stress test completed.")
    stats = environment.runner.stats.total
    print(f"Requests: {stats.num_requests}, Failures: {stats.num_failures}")
    print(f"Average response time: {stats.avg_response_time:.2f}ms")
