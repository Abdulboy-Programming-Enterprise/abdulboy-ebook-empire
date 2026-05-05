"""
User Model Service
==================
Business logic for user operations.
"""

from typing import Optional
from services.users.repository import UserRepository
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service for user business logic."""
    
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def authenticate(self, email: str, password: str):
        """Authenticate user."""
        user = await self.repository.get_by_email(email)
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if user.deleted_at:
            return None
        
        return user
    
    async def create_user(self, email: str, password: str, full_name: str, account_type: str = "normal"):
        """Create a new user."""
        existing = await self.repository.get_by_email(email)
        if existing:
            raise ValueError("User already exists")
        
        user_data = {
            "email": email.lower(),
            "password_hash": get_password_hash(password),
            "full_name": full_name,
            "account_type": account_type,
        }
        
        return await self.repository.create(user_data)
    
    async def update_profile(self, user_id: str, update_data: dict):
        """Update user profile."""
        return await self.repository.update(user_id, update_data)
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password."""
        user = await self.repository.get_by_id(user_id)
        
        if not user:
            return False
        
        if not verify_password(current_password, user.password_hash):
            return False
        
        update_data = {"password_hash": get_password_hash(new_password)}
        await self.repository.update(user_id, update_data)
        
        return True
