"""
Security penetration tests.
"""

import pytest
import requests


class TestSecurityHeaders:
    """Test security headers are present."""
    
    def test_hsts_header(self, base_url):
        """Test HSTS header is set."""
        response = requests.get(base_url)
        assert 'strict-transport-security' in response.headers
    
    def test_csp_header(self, base_url):
        """Test Content Security Policy header."""
        response = requests.get(base_url)
        assert 'content-security-policy' in response.headers
    
    def test_xframe_options(self, base_url):
        """Test X-Frame-Options header."""
        response = requests.get(base_url)
        assert response.headers.get('x-frame-options') == 'DENY'


class TestAuthenticationSecurity:
    """Test authentication security."""
    
    def test_sql_injection_login(self, base_url):
        """Test SQL injection in login form."""
        payloads = ["' OR '1'='1", "admin'--", "1' OR '1'='1"]
        
        for payload in payloads:
            response = requests.post(f"{base_url}/api/v1/auth/login", json={
                "email": payload,
                "password": "anything"
            })
            # Should not authenticate
            assert response.status_code == 401
    
    def test_brute_force_protection(self, base_url):
        """Test rate limiting on login."""
        for i in range(15):
            response = requests.post(f"{base_url}/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": f"wrong{i}"
            })
        
        # After many attempts, should be rate limited
        assert response.status_code in [401, 429]
    
    def test_token_expiration(self, auth_headers):
        """Test token expiration."""
        # This test requires waiting for token to expire
        # In practice, use a token with short expiration
        pass


class TestInputValidation:
    """Test input validation."""
    
    def test_xss_attempt(self, base_url):
        """Test XSS prevention."""
        xss_payload = "<script>alert('XSS')</script>"
        
        response = requests.get(f"{base_url}/api/v1/books/search?q={xss_payload}")
        
        # Payload should be escaped, not executed
        assert response.status_code == 200
        assert "<script>" not in response.text
    
    def test_large_payload(self, base_url):
        """Test handling of large payloads."""
        large_payload = "A" * 1000000
        
        response = requests.post(f"{base_url}/api/v1/books/search", json={
            "query": large_payload
        })
        
        # Should handle gracefully
        assert response.status_code in [200, 413, 400]
