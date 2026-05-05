"""
PDF Processor Module
====================
PDF manipulation utilities for book previews, thumbnails, and page counting.
"""

import io
import os
import tempfile
from typing import Optional, Tuple, List
from PIL import Image
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from app.core.logger import logger


def count_pdf_pages(pdf_path: str) -> int:
    """
    Count total pages in a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Number of pages
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)
    except Exception as e:
        logger.error(f"Failed to count PDF pages: {e}")
        return 0


def extract_pdf_preview(
    pdf_path: str,
    output_path: str,
    num_pages: int = 10,
    start_page: int = 0
) -> bool:
    """
    Extract a preview (first N pages) from a PDF.
    
    Args:
        pdf_path: Path to source PDF
        output_path: Path for output preview PDF
        num_pages: Number of pages to extract
        start_page: Starting page index (0-based)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(pdf_path, 'rb') as infile:
            reader = PyPDF2.PdfReader(infile)
            writer = PyPDF2.PdfWriter()
            
            total_pages = len(reader.pages)
            end_page = min(start_page + num_pages, total_pages)
            
            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])
            
            with open(output_path, 'wb') as outfile:
                writer.write(outfile)
        
        return True
    except Exception as e:
        logger.error(f"Failed to extract PDF preview: {e}")
        return False


def generate_pdf_thumbnail(
    pdf_path: str,
    output_path: str,
    page_num: int = 0,
    size: Tuple[int, int] = (200, 300)
) -> bool:
    """
    Generate a thumbnail image from the first page of a PDF.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Path for output image
        page_num: Page number to use (0-based)
        size: Desired thumbnail size (width, height)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # This is a simplified version - for production, use pdf2image
        # or a more robust PDF rendering library
        from pdf2image import convert_from_path
        
        images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)
        
        if images:
            img = images[0]
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path, 'JPEG', quality=85)
            return True
        
        return False
    except ImportError:
        # Fallback: create a placeholder image
        logger.warning("pdf2image not installed, creating placeholder thumbnail")
        img = Image.new('RGB', size, color=(200, 200, 200))
        img.save(output_path, 'JPEG')
        return True
    except Exception as e:
        logger.error(f"Failed to generate PDF thumbnail: {e}")
        return False


def merge_pdfs(pdf_paths: List[str], output_path: str) -> bool:
    """
    Merge multiple PDF files into one.
    
    Args:
        pdf_paths: List of PDF file paths
        output_path: Path for merged PDF
        
    Returns:
        True if successful, False otherwise
    """
    try:
        writer = PyPDF2.PdfWriter()
        
        for path in pdf_paths:
            with open(path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    writer.add_page(page)
        
        with open(output_path, 'wb') as outfile:
            writer.write(outfile)
        
        return True
    except Exception as e:
        logger.error(f"Failed to merge PDFs: {e}")
        return False


def add_watermark_to_pdf(
    pdf_path: str,
    output_path: str,
    watermark_text: str
) -> bool:
    """
    Add a text watermark to a PDF file.
    
    Args:
        pdf_path: Path to source PDF
        output_path: Path for watermarked PDF
        watermark_text: Text to use as watermark
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create watermark PDF
        watermark_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        
        c = canvas.Canvas(watermark_pdf.name, pagesize=letter)
        c.setFont("Helvetica", 36)
        c.setFillColorRGB(0.7, 0.7, 0.7, alpha=0.3)
        
        # Rotate and position watermark
        c.saveState()
        c.translate(letter[0] / 2, letter[1] / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, watermark_text)
        c.restoreState()
        c.save()
        
        # Merge watermark with PDF
        with open(pdf_path, 'rb') as infile:
            reader = PyPDF2.PdfReader(infile)
            writer = PyPDF2.PdfWriter()
            
            with open(watermark_pdf.name, 'rb') as watermark_file:
                watermark_reader = PyPDF2.PdfReader(watermark_file)
                watermark_page = watermark_reader.pages[0]
                
                for page in reader.pages:
                    page.merge_page(watermark_page)
                    writer.add_page(page)
            
            with open(output_path, 'wb') as outfile:
                writer.write(outfile)
        
        # Clean up temporary file
        os.unlink(watermark_pdf.name)
        
        return True
    except Exception as e:
        logger.error(f"Failed to add watermark to PDF: {e}")
        return False


def extract_text_from_pdf(pdf_path: str, page_limit: Optional[int] = None) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        page_limit: Maximum number of pages to extract
        
    Returns:
        Extracted text content
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text_parts = []
            
            page_count = len(reader.pages)
            if page_limit:
                page_count = min(page_count, page_limit)
            
            for page_num in range(page_count):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return ""

def get_pdf_metadata(pdf_path: str) -> dict:
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary of metadata
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            info = reader.metadata
            return {
                'title': info.get('/Title', ''),
                'author': info.get('/Author', ''),
                'subject': info.get('/Subject', ''),
                'creator': info.get('/Creator', ''),
                'producer': info.get('/Producer', ''),
                'page_count': len(reader.pages),
            }
    except Exception as e:
        logger.error(f"Failed to extract PDF metadata: {e}")
        return {}
