#!/usr/bin/env python
"""
Development Seed Script - Load test data for development
"""

import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.models.book import Book
from app.core.security import get_password_hash


async def seed_dev_data():
    db = SessionLocal()
    
    # Create test user
    test_user = User(
        email="dev@example.com",
        password_hash=get_password_hash("DevPass123!"),
        full_name="Developer User"
    )
    db.add(test_user)
    
    # Create sample books
    books = [
        Book(title="Python Programming", slug="python-programming", author_name="John Doe", total_pages=300),
        Book(title="Web Development", slug="web-development", author_name="Jane Smith", total_pages=250),
    ]
    for book in books:
        db.add(book)
    
    await db.commit()
    print("Development data seeded")
    await db.close()


if __name__ == "__main__":
    asyncio.run(seed_dev_data())
