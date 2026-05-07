"""
Unit tests for gamification engine.
"""

import pytest
from services.gamification.badge_engine import BadgeEngine
from services.gamification.point_system import PointSystem


@pytest.mark.unit
class TestBadgeEngine:
    """Test badge engine functionality."""
    
    @pytest.fixture
    def badge_engine(self, db_session):
        """Create badge engine instance."""
        return BadgeEngine(db_session)
    
    async def test_check_criteria_books_read(self, badge_engine, test_user):
        """Test badge criteria for books read."""
        stats = {"books_read": 10}
        
        # Should pass for badge requiring 5 books
        meets = await badge_engine._check_criteria(
            mock_badge(criteria_type="books_read", criteria_value=5),
            stats, "book_read", None
        )
        assert meets is True
        
        # Should fail for badge requiring 20 books
        meets = await badge_engine._check_criteria(
            mock_badge(criteria_type="books_read", criteria_value=20),
            stats, "book_read", None
        )
        assert meets is False
    
    async def test_check_criteria_points(self, badge_engine, test_user):
        """Test badge criteria for total points."""
        stats = {"total_points": 1500}
        
        meets = await badge_engine._check_criteria(
            mock_badge(criteria_type="total_points", criteria_value=1000),
            stats, "point_earned", None
        )
        assert meets is True


@pytest.mark.unit
class TestPointSystem:
    """Test point system functionality."""
    
    @pytest.fixture
    def point_system(self, db_session):
        """Create point system instance."""
        return PointSystem(db_session)
    
    async def test_award_purchase_points(self, point_system, test_user):
        """Test awarding points for purchase."""
        points = await point_system.award_purchase_points(test_user.id, 25.00)
        
        # 10 points per dollar = 250 points
        assert points >= 250
    
    async def test_award_review_points(self, point_system, test_user):
        """Test awarding points for review."""
        points = await point_system.award_review_points(test_user.id)
        
        assert points == 50
    
    async def test_get_user_points(self, point_system, test_user):
        """Test retrieving user points."""
        total = await point_system.get_user_points(test_user.id)
        
        assert isinstance(total, int)
        assert total >= 0


def mock_badge(criteria_type, criteria_value):
    """Create mock badge for testing."""
    class MockBadge:
        criteria_type = criteria_type
        criteria_value = criteria_value
    return MockBadge()
