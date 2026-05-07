"""
Pytest Configuration
====================
Shared fixtures and configuration for all tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.app import create_app
from app.core.database import get_db, Base
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def app():
    """Create FastAPI app instance for testing."""
    return create_app()


@pytest.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def sync_client(app):
    """Create sync test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user_data():
    """Sample user data for tests."""
    return {
        "email": "test@example.com",
        "password": "Test123456!",
        "confirm_password": "Test123456!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_book_data():
    """Sample book data for tests."""
    return {
        "title": "Test Book",
        "author_name": "Test Author",
        "total_pages": 100,
        "preview_pages": 10,
        "price": 9.99,
        "description": "This is a test book description."
    }
