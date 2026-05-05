"""
Suggestion Engine
=================
AI-powered recommendation engine using collaborative and content-based filtering.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict
import pickle
import os
from datetime import datetime
from app.models.book import Book, BookStatus
from app.models.payment import UserBookPurchase
from app.models.suggestion import SuggestionLog
from app.core.logger import logger


class SuggestionEngine:
    """AI-powered recommendation engine."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_path = "/storage/data/ml-models/"
        self.similarity_matrix = None
        self.user_preferences = {}
    
    async def initialize(self):
        """Initialize the recommendation engine."""
        await self._load_models()
        logger.info("Suggestion engine initialized")
    
    async def _load_models(self):
        """Load pre-trained models from disk."""
        similarity_path = os.path.join(self.model_path, "similarity_matrix.pkl")
        if os.path.exists(similarity_path):
            try:
                with open(similarity_path, 'rb') as f:
                    self.similarity_matrix = pickle.load(f)
                logger.info("Loaded similarity matrix")
            except Exception as e:
                logger.error(f"Failed to load similarity matrix: {e}")
    
    async def get_recommendations(
        self,
        user_id: str,
        purchased_book_ids: List[str],
        viewed_book_ids: List[str] = None,
        limit: int = 10
    ) -> List[Book]:
        """
        Get personalized book recommendations for a user.
        
        Uses hybrid approach: collaborative filtering + content-based.
        """
        if not purchased_book_ids and not viewed_book_ids:
            # New user - return popular books
            return await self._get_popular_books(limit)
        
        # Get collaborative recommendations from similar users
        collab_recs = await self._get_collaborative_recommendations(
            user_id, purchased_book_ids, limit * 2
        )
        
        # Get content-based recommendations from user's history
        content_recs = await self._get_content_based_recommendations(
            purchased_book_ids + (viewed_book_ids or []), limit * 2
        )
        
        # Combine and deduplicate
        recommended_ids = set()
        recommendations = []
        
        for book in collab_recs + content_recs:
            if str(book.id) not in recommended_ids and str(book.id) not in purchased_book_ids:
                recommended_ids.add(str(book.id))
                recommendations.append(book)
                if len(recommendations) >= limit:
                    break
        
        return recommendations
    
    async def _get_collaborative_recommendations(
        self,
        user_id: str,
        purchased_book_ids: List[str],
        limit: int
    ) -> List[Book]:
        """
        Get recommendations based on what similar users purchased.
        """
        if not purchased_book_ids:
            return []
        
        # Find users who purchased similar books
        similar_users_query = (
            select(UserBookPurchase.user_id)
            .where(UserBookPurchase.book_id.in_(purchased_book_ids))
            .where(UserBookPurchase.user_id != user_id)
            .group_by(UserBookPurchase.user_id)
            .order_by(func.count().desc())
            .limit(50)
        )
        
        result = await self.db.execute(similar_users_query)
        similar_user_ids = [row[0] for row in result.all()]
        
        if not similar_user_ids:
            return []
        
        # Get books purchased by similar users
        recommendations_query = (
            select(Book)
            .join(UserBookPurchase, UserBookPurchase.book_id == Book.id)
            .where(
                UserBookPurchase.user_id.in_(similar_user_ids),
                Book.status == BookStatus.PUBLISHED,
                Book.deleted_at.is_(None),
                Book.id.not_in(purchased_book_ids)
            )
            .group_by(Book.id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        
        result = await self.db.execute(recommendations_query)
        return result.scalars().all()
    
    async def _get_content_based_recommendations(
        self,
        source_book_ids: List[str],
        limit: int
    ) -> List[Book]:
        """
        Get recommendations based on book attributes (author, tags, etc.).
        """
        if not source_book_ids:
            return []
        
        # Get source books
        result = await self.db.execute(
            select(Book).where(Book.id.in_(source_book_ids))
        )
        source_books = result.scalars().all()
        
        if not source_books:
            return []
        
        # Extract author preferences
        authors = [book.author_name for book in source_books]
        
        # Find books by same authors
        recommendations_query = (
            select(Book)
            .where(
                Book.status == BookStatus.PUBLISHED,
                Book.deleted_at.is_(None),
                Book.id.not_in(source_book_ids),
                Book.author_name.in_(authors)
            )
            .order_by(Book.downloads_count.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(recommendations_query)
        books = result.scalars().all()
        
        if len(books) < limit:
            # Add popular books to fill gap
            popular = await self._get_popular_books(limit - len(books))
            books.extend(popular)
        
        return books
    
    async def _get_popular_books(self, limit: int) -> List[Book]:
        """Get most popular books overall."""
        result = await self.db.execute(
            select(Book)
            .where(
                Book.status == BookStatus.PUBLISHED,
                Book.deleted_at.is_(None)
            )
            .order_by(Book.downloads_count.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_similar_books(
        self,
        book_id: str,
        limit: int = 10
    ) -> List[Book]:
        """
        Get books similar to a given book using content-based filtering.
        """
        # Get source book
        result = await self.db.execute(select(Book).where(Book.id == book_id))
        source_book = result.scalar_one_or_none()
        
        if not source_book:
            return []
        
        # Use similarity matrix if available
        if self.similarity_matrix and str(book_id) in self.similarity_matrix:
            similar_ids = self.similarity_matrix[str(book_id)][:limit*2]
            result = await self.db.execute(
                select(Book).where(
                    Book.id.in_(similar_ids),
                    Book.status == BookStatus.PUBLISHED
                )
            )
            books = result.scalars().all()
            if books:
                return books[:limit]
        
        # Fallback: same author or same language
        recommendations_query = (
            select(Book)
            .where(
                Book.status == BookStatus.PUBLISHED,
                Book.deleted_at.is_(None),
                Book.id != book_id,
                (
                    (Book.author_name == source_book.author_name) |
                    (Book.language == source_book.language)
                )
            )
            .order_by(Book.downloads_count.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(recommendations_query)
        books = result.scalars().all()
        
        if len(books) < limit:
            # Add popular books to fill gap
            popular = await self._get_popular_books(limit - len(books))
            books.extend(popular)
        
        return books
    
    async def update_model(self) -> Dict[str, Any]:
        """
        Update the recommendation model with new user interaction data.
        """
        try:
            # Build similarity matrix based on purchase patterns
            await self._build_similarity_matrix()
            
            logger.info("Recommendation model updated successfully")
            return {"status": "success", "message": "Model updated"}
            
        except Exception as e:
            logger.error(f"Failed to update recommendation model: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _build_similarity_matrix(self):
        """Build book similarity matrix based on co-purchase patterns."""
        # Get all purchase data
        result = await self.db.execute(
            select(UserBookPurchase.book_id, UserBookPurchase.user_id)
        )
        purchases = result.all()
        
        # Build user-item matrix
        user_items = defaultdict(set)
        item_users = defaultdict(set)
        
        for book_id, user_id in purchases:
            user_items[user_id].add(book_id)
            item_users[book_id].add(user_id)
        
        # Calculate similarity between books using Jaccard index
        similarity = defaultdict(dict)
        book_ids = list(item_users.keys())
        
        for i, book_a in enumerate(book_ids):
            for book_b in book_ids[i+1:]:
                users_a = item_users[book_a]
                users_b = item_users[book_b]
                
                intersection = len(users_a & users_b)
                union = len(users_a | users_b)
                
                if union > 0:
                    jaccard = intersection / union
                    if jaccard > 0.1:  # Only store meaningful similarities
                        similarity[book_a][book_b] = jaccard
                        similarity[book_b][book_a] = jaccard
        
        # Save similarity matrix
        os.makedirs(self.model_path, exist_ok=True)
        with open(os.path.join(self.model_path, "similarity_matrix.pkl"), 'wb') as f:
            pickle.dump(similarity, f)
        
        self.similarity_matrix = similarity
        logger.info(f"Built similarity matrix with {len(similarity)} books")
