"""
User Service
============
High-level user management service.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from services.users.repository import UserRepository
from services.users.user import UserService
from app.models.user import User


class UserManagementService:
    """High-level service for user management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)
        self.user_service = UserService(self.repository)
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return await self.repository.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.repository.get_by_email(email)
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        account_type: str = "normal"
    ) -> User:
        """Create a new user."""
        return await self.user_service.create_user(email, password, full_name, account_type)
    
    async def update_user(self, user_id: str, update_data: dict) -> Optional[User]:
        """Update user information."""
        return await self.repository.update(user_id, update_data)
    
    async def delete_user(self, user_id: str) -> bool:
        """Soft delete user."""
        return await self.repository.delete(user_id)
    
    async def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        account_type: Optional[str] = None
    ) -> tuple[List[User], int]:
        """List users with pagination."""
        return await self.repository.list_users(page, limit, search, account_type)
    
    async def get_user_stats(self) -> dict:
        """Get user statistics."""
        users, total = await self.repository.list_users(limit=1)
        return {
            "total_users": total,
        }
