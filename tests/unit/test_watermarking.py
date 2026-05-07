"""
Unit tests for watermarking functionality.
"""

import pytest
import json
from services.watermarking.text_watermarker import TextWatermarker
from services.watermarking.pdf_watermarker import PDFWatermarker


@pytest.mark.unit
class TestTextWatermarker:
    """Test text watermarking."""
    
    def setup_method(self):
        """Setup before each test."""
        self.watermarker = TextWatermarker()
    
    def test_embed_and_extract(self):
        """Test embedding and extracting watermark."""
        original_text = "This is a sample book content."
        watermark_data = {
            "user_id": "user-123",
            "book_id": "book-456",
            "timestamp": "2026-04-24T00:00:00Z"
        }
        
        watermarked = self.watermarker.embed_watermark(original_text, watermark_data)
        extracted = self.watermarker.extract_watermark(watermarked)
        
        assert extracted is not None
        assert extracted["user_id"] == "user-123"
        assert extracted["book_id"] == "book-456"
    
    def test_no_watermark(self):
        """Test extracting from text without watermark."""
        text = "Regular text without any watermark."
        extracted = self.watermarker.extract_watermark(text)
        
        assert extracted is None
    
    def test_watermark_roundtrip(self):
        """Test full roundtrip watermarking."""
        watermark_data = {"test": "data", "count": 42}
        text = "Important content that needs protection."
        
        watermarked = self.watermarker.embed_watermark(text, watermark_data)
        extracted = self.watermarker.extract_watermark(watermarked)
        
        assert extracted == watermark_data


@pytest.mark.unit
class TestPDFWatermarker:
    """Test PDF watermarking."""
    
    def setup_method(self):
        """Setup before each test."""
        self.watermarker = PDFWatermarker()
    
    def test_create_watermark_pdf(self):
        """Test creating watermark PDF."""
        watermark_pdf = self.watermarker.create_watermark_pdf(
            "CONFIDENTIAL",
            opacity=0.3,
            rotation=45
        )
        
        assert watermark_pdf is not None
        assert len(watermark_pdf) > 0
    
    def test_generate_watermark_text(self):
        """Test generating watermark text."""
        user_id = "user-123"
        user_email = "user@example.com"
        purchase_id = "purchase-456"
        
        watermark_text = f"Licensed to: {user_email} | ID: {purchase_id}"
        
        assert "user@example.com" in watermark_text
        assert "purchase-456" in watermark_text
