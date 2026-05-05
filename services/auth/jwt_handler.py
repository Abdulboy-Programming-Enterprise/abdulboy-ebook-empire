"""
JWT Handler Service
===================
JWT token generation, validation, and management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from app.core.config import settings


class JWTHandler:
    """Handles JWT token operations."""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create an access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    def verify_access_token(self, token: str) -> Optional[str]:
        """Verify access token and return user ID."""
        payload = self.decode_token(token)
        if payload and payload.get("type") == "access":
            return payload.get("sub")
        return None
    
    def verify_refresh_token(self, token: str) -> Optional[str]:
        """Verify refresh token and return user ID."""
        payload = self.decode_token(token)
        if payload and payload.get("type") == "refresh":
            return payload.get("sub")
        return None
