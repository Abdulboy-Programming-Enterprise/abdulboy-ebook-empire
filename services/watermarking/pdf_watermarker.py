"""
PDF Watermarker
===============
Adds watermarks to PDF documents.
"""

import io
from typing import Optional, Dict, Any
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter
import os
import tempfile
from datetime import datetime


class PDFWatermarker:
    """Adds watermarks to PDF documents."""
    
    def __init__(self):
        self.default_opacity = 0.3
        self.default_font_size = 36
        self.default_position = "center"
    
    def create_watermark_pdf(
        self,
        text: str,
        page_size: tuple = letter,
        opacity: float = 0.3,
        rotation: int = 45
    ) -> bytes:
        """
        Create a watermark PDF layer.
        
        Args:
            text: Watermark text
            page_size: Page size (width, height)
            opacity: Text opacity
            rotation: Rotation angle in degrees
            
        Returns:
            PDF bytes of watermark layer
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=page_size)
        
        # Set text properties
        c.setFont("Helvetica", self.default_font_size)
        c.setFillColorRGB(0.7, 0.7, 0.7, alpha=opacity)
        
        # Calculate center position
        width, height = page_size
        
        # Rotate and draw
        c.saveState()
        c.translate(width / 2, height / 2)
        c.rotate(rotation)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def add_watermark(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        watermark_text: str,
        opacity: float = 0.3,
        rotation: int = 45
    ) -> bool:
        """
        Add watermark to all pages of a PDF.
        
        Args:
            input_pdf_path: Path to input PDF
            output_pdf_path: Path for output PDF
            watermark_text: Text to use as watermark
            opacity: Watermark opacity
            rotation: Watermark rotation angle
            
        Returns:
            True if successful
        """
        try:
            # Create watermark layer
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()
            
            # Get first page to determine size
            first_page = reader.pages[0]
            page_size = (
                float(first_page.mediabox.width),
                float(first_page.mediabox.height)
            )
            
            # Create watermark PDF
            watermark_pdf = self.create_watermark_pdf(
                watermark_text,
                page_size,
                opacity,
                rotation
            )
            
            watermark_reader = PdfReader(io.BytesIO(watermark_pdf))
            watermark_page = watermark_reader.pages[0]
            
            # Apply watermark to each page
            for page in reader.pages:
                page.merge_page(watermark_page)
                writer.add_page(page)
            
            # Write output
            with open(output_pdf_path, 'wb') as f:
                writer.write(f)
            
            return True
            
        except Exception as e:
            print(f"Failed to add PDF watermark: {e}")
            return False
    
    def add_user_watermark(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        user_id: str,
        user_email: str,
        purchase_id: str
    ) -> bool:
        """
        Add user-specific watermark for DRM.
        
        Args:
            input_pdf_path: Path to input PDF
            output_pdf_path: Path for output PDF
            user_id: User identifier
            user_email: User email
            purchase_id: Purchase identifier
            
        Returns:
            True if successful
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        watermark_text = f"Licensed to: {user_email} | Purchase ID: {purchase_id} | {timestamp}"
        
        return self.add_watermark(
            input_pdf_path,
            output_pdf_path,
            watermark_text,
            opacity=0.2,
            rotation=30
        )
