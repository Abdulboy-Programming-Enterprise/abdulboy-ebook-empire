"""
Suggestion Tasks
================
Celery tasks for AI recommendation engine updates.
"""

from celery import shared_task
from app.services.ai.suggestion_engine import SuggestionEngine
from app.core.database import SessionLocal
from app.core.logger import logger


@shared_task(name="update_recommendation_model")
def update_recommendation_model():
    """
    Update the recommendation model with new user data.
    """
    try:
        db = SessionLocal()
        engine = SuggestionEngine(db)
        
        result = engine.update_model()
        
        logger.info("Recommendation model updated successfully")
        db.close()
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Failed to update recommendation model: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="generate_user_recommendations")
def generate_user_recommendations(user_id: str):
    """
    Generate personalized recommendations for a specific user.
    """
    try:
        db = SessionLocal()
        engine = SuggestionEngine(db)
        
        recommendations = engine.get_recommendations(user_id, limit=20)
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        db.close()
        
        return {"status": "success", "recommendations_count": len(recommendations)}
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations for user {user_id}: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="update_similarity_matrix")
def update_similarity_matrix():
    """
    Update the book similarity matrix for content-based recommendations.
    """
    try:
        db = SessionLocal()
        engine = SuggestionEngine(db)
        
        result = engine.update_similarity_matrix()
        
        logger.info("Similarity matrix updated successfully")
        db.close()
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Failed to update similarity matrix: {e}")
        return {"status": "error", "error": str(e)}
