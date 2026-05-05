"""
Base Model Module
=================
Base SQLAlchemy model classes with common fields and mixins.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
import uuid
from app.core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    deleted_at = Column(DateTime, nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self):
        self.deleted_at = datetime.utcnow()


class UUIDMixin:
    """Mixin for UUID primary keys."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class BaseModel(Base, TimestampMixin, UUIDMixin):
    """Abstract base model with common fields."""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
