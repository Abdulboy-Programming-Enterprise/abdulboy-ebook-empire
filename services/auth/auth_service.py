"""
Authentication Service
======================
User authentication and authorization logic.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.services.auth.jwt_handler import JWTHandler


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jwt_handler = JWTHandler()
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if user.deleted_at:
            return None
        
        return user
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        account_type: str = "normal"
    ) -> User:
        """Create a new user."""
        new_user = User(
            email=email.lower(),
            password_hash=get_password_hash(password),
            full_name=full_name,
            account_type=account_type,
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        return new_user
    
    def generate_tokens(self, user_id: str) -> dict:
        """Generate access and refresh tokens for user."""
        return {
            "access_token": self.jwt_handler.create_access_token({"sub": user_id}),
            "refresh_token": self.jwt_handler.create_refresh_token({"sub": user_id}),
            "token_type": "bearer"
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token."""
        user_id = self.jwt_handler.verify_refresh_token(refresh_token)
        
        if not user_id:
            return None
        
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or user.deleted_at:
            return None
        
        return self.jwt_handler.create_access_token({"sub": user_id})
