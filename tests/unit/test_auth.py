"""
Unit tests for authentication functionality.
"""

import pytest
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.config import settings


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePass123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
    
    def test_verify_wrong_password(self):
        """Test password verification with wrong password."""
        password = "CorrectPass123!"
        wrong_password = "WrongPass123!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_empty_password(self):
        """Test empty password handling."""
        with pytest.raises(ValueError):
            get_password_hash("")


@pytest.mark.unit
class TestJWT:
    """Test JWT token functions."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user-123"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        data = {"sub": "user-123", "test": "value"}
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["test"] == "value"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        decoded = decode_token(invalid_token)
        
        assert decoded is None
    
    def test_token_expiration(self):
        """Test token expiration handling."""
        from datetime import timedelta
        data = {"sub": "user-123"}
        # Create token with very short expiration (1 second)
        token = create_access_token(data, expires_delta=timedelta(seconds=1))
        
        # Should decode immediately
        assert decode_token(token) is not None
