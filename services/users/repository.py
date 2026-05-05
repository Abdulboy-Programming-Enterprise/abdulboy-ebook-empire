"""
User Repository
===============
Database operations for user management.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.user import User


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()
    
    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update(self, user_id: str, update_data: dict) -> Optional[User]:
        """Update user information."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Soft delete user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        from datetime import datetime
        user.deleted_at = datetime.utcnow()
        await self.db.commit()
        return True
    
    async def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        account_type: Optional[str] = None
    ) -> tuple[List[User], int]:
        """List users with pagination and filtering."""
        query = select(User).where(User.deleted_at.is_(None))
        
        if search:
            query = query.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )
        
        if account_type:
            query = query.where(User.account_type == account_type)
        
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return users, total or 0
