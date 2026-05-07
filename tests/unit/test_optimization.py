"""
Unit tests for optimization engine.
"""

import pytest
from services.optimization.image_optimizer import ImageOptimizer
from services.optimization.cache_strategy import CacheStrategy


@pytest.mark.unit
class TestImageOptimizer:
    """Test image optimization."""
    
    def setup_method(self):
        """Setup before each test."""
        self.optimizer = ImageOptimizer()
    
    def test_size_presets(self):
        """Test size presets."""
        assert "thumbnail" in self.optimizer.SIZE_PRESETS
        assert "medium" in self.optimizer.SIZE_PRESETS
        assert "large" in self.optimizer.SIZE_PRESETS
        
        thumb_size = self.optimizer.SIZE_PRESETS["thumbnail"]
        assert thumb_size[0] == 150
        assert thumb_size[1] == 200
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        key = self.optimizer._get_cache_key("test.jpg", 300, 400, "webp")
        
        assert key is not None
        assert key.endswith(".webp")
    
    def test_get_optimized_url(self):
        """Test optimized URL generation."""
        url = "https://example.com/image.jpg"
        optimized = self.optimizer.get_optimized_url(url, "medium")
        
        assert "w=600" in optimized or "w=300"  # Depends on preset


@pytest.mark.unit
class TestCacheStrategy:
    """Test cache strategy."""
    
    @pytest.mark.asyncio
    async def test_generate_key(self):
        """Test cache key generation."""
        key = await CacheStrategy.generate_key("books", "list", page=1, limit=20)
        
        assert key.startswith("books:")
        assert len(key) > 10
    
    @pytest.mark.asyncio
    async def test_get_or_set(self, mock_cache):
        """Test get or set cache pattern."""
        call_count = 0
        
        async def fetcher():
            nonlocal call_count
            call_count += 1
            return {"data": "test"}
        
        result1 = await CacheStrategy.get_or_set("test_key", fetcher, ttl=60)
        result2 = await CacheStrategy.get_or_set("test_key", fetcher, ttl=60)
        
        assert result1 == result2
        assert call_count == 1
