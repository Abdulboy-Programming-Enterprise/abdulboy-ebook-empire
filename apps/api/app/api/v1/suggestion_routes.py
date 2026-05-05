"""
Suggestion Routes
=================
AI-powered book recommendation endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.book import Book, BookStatus
from app.models.suggestion import SuggestionLog
from app.models.payment import UserBookPurchase
from app.schemas.book import BookResponse
from app.schemas.response import StandardResponse
from app.api.deps import get_current_user
from app.services.ai.suggestion_engine import SuggestionEngine
from app.core.logger import logger

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])


@router.get("/for-you", response_model=StandardResponse)
async def get_personalized_suggestions(
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get personalized book recommendations for the current user.
    """
    suggestion_engine = SuggestionEngine(db)
    
    # Get user's reading history
    purchase_result = await db.execute(
        select(UserBookPurchase.book_id)
        .where(UserBookPurchase.user_id == current_user.id)
        .limit(10)
    )
    purchased_book_ids = [str(row[0]) for row in purchase_result.all()]
    
    # Get user's viewed books from analytics (simplified)
    viewed_book_ids = []  # Would come from analytics service
    
    # Generate recommendations
    recommendations = await suggestion_engine.get_recommendations(
        user_id=str(current_user.id),
        purchased_book_ids=purchased_book_ids,
        viewed_book_ids=viewed_book_ids,
        limit=limit
    )
    
    # Log suggestions
    for book in recommendations:
        suggestion_log = SuggestionLog(
            user_id=current_user.id,
            book_id=book.id,
            suggestion_type="personalized",
            confidence_score=0.8,
            created_at=datetime.utcnow(),
        )
        db.add(suggestion_log)
    await db.commit()
    
    # Build response
    book_responses = []
    for book in recommendations:
        book_responses.append({
            "id": str(book.id),
            "title": book.title,
            "slug": book.slug,
            "author_name": book.author_name,
            "cover_image_url": book.cover_image_url,
            "price": book.price,
            "is_free": book.is_free,
        })
    
    return StandardResponse(
        success=True,
        data={
            "suggestions": book_responses,
            "total": len(book_responses),
        }
    )


@router.get("/similar/{book_id}", response_model=StandardResponse)
async def get_similar_books(
    book_id: str,
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get books similar to a given book.
    """
    # Get the source book
    result = await db.execute(select(Book).where(Book.id == book_id))
    source_book = result.scalar_one_or_none()
    
    if not source_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    suggestion_engine = SuggestionEngine(db)
    similar_books = await suggestion_engine.get_similar_books(
        book_id=book_id,
        limit=limit
    )
    
    book_responses = []
    for book in similar_books:
        book_responses.append({
            "id": str(book.id),
            "title": book.title,
            "slug": book.slug,
            "author_name": book.author_name,
            "cover_image_url": book.cover_image_url,
            "price": book.price,
            "is_free": book.is_free,
        })
    
    return StandardResponse(
        success=True,
        data={
            "source_book": {
                "id": str(source_book.id),
                "title": source_book.title,
                "author": source_book.author_name,
            },
            "similar_books": book_responses,
        }
    )


@router.get("/popular", response_model=StandardResponse)
async def get_popular_books(
    limit: int = Query(10, ge=1, le=20),
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get most popular books based on downloads and views.
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Book)
        .where(
            Book.status == BookStatus.PUBLISHED,
            Book.published_at >= cutoff_date
        )
        .order_by(
            desc(Book.downloads_count + Book.views_count * 0.1)
        )
        .limit(limit)
    )
    popular_books = result.scalars().all()
    
    book_responses = []
    for book in popular_books:
        book_responses.append({
            "id": str(book.id),
            "title": book.title,
            "author_name": book.author_name,
            "cover_image_url": book.cover_image_url,
            "price": book.price,
            "is_free": book.is_free,
            "downloads": book.downloads_count,
        })
    
    return StandardResponse(
        success=True,
        data={
            "popular_books": book_responses,
            "period_days": days,
        }
    )


@router.post("/track-click")
async def track_suggestion_click(
    suggestion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Track when a user clicks on a suggestion.
    """
    result = await db.execute(select(SuggestionLog).where(SuggestionLog.id == suggestion_id))
    suggestion = result.scalar_one_or_none()
    
    if suggestion and suggestion.user_id == current_user.id:
        suggestion.was_clicked = True
        suggestion.clicked_at = datetime.utcnow()
        await db.commit()
    
    return StandardResponse(success=True, message="Tracked")
