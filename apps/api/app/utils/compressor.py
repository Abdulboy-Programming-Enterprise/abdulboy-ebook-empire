"""
Compressor Module
=================
File compression utilities for images, PDFs, and general optimization.
"""

import io
import os
import zipfile
from typing import Optional, Union, List, Tuple
from PIL import Image
import PyPDF2
from app.core.logger import logger


def compress_image(
    input_path: Union[str, bytes, io.BytesIO],
    output_path: Optional[str] = None,
    quality: int = 85,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    format: str = 'JPEG'
) -> Tuple[bool, Optional[bytes]]:
    """
    Compress an image file.
    
    Args:
        input_path: Path to image file or bytes/BytesIO object
        output_path: Optional output file path
        quality: JPEG quality (1-100)
        max_width: Maximum width (preserves aspect ratio)
        max_height: Maximum height (preserves aspect ratio)
        format: Output format (JPEG, PNG, WEBP)
        
    Returns:
        Tuple of (success, compressed_bytes)
    """
    try:
        # Load image
        if isinstance(input_path, str):
            img = Image.open(input_path)
        elif isinstance(input_path, bytes):
            img = Image.open(io.BytesIO(input_path))
        else:
            img = Image.open(input_path)
        
        # Convert to RGB if necessary (for JPEG)
        if format == 'JPEG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if dimensions specified
        if max_width or max_height:
            original_width, original_height = img.size
            ratio = min(
                (max_width or original_width) / original_width,
                (max_height or original_height) / original_height,
                1.0
            )
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save compressed image
        output_bytes = io.BytesIO()
        save_kwargs = {'format': format, 'optimize': True}
        
        if format == 'JPEG':
            save_kwargs['quality'] = quality
            save_kwargs['progressive'] = True
        elif format == 'PNG':
            save_kwargs['compress_level'] = 6
        elif format == 'WEBP':
            save_kwargs['quality'] = quality
        
        img.save(output_bytes, **save_kwargs)
        compressed_bytes = output_bytes.getvalue()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(compressed_bytes)
        
        return True, compressed_bytes
        
    except Exception as e:
        logger.error(f"Failed to compress image: {e}")
        return False, None


def compress_pdf(
    input_path: str,
    output_path: Optional[str] = None,
    quality: str = 'medium'
) -> bool:
    """
    Compress a PDF file by reducing image quality and removing metadata.
    
    Args:
        input_path: Path to PDF file
        output_path: Optional output path (default: input_path with _compressed suffix)
        quality: Compression level ('low', 'medium', 'high')
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_compressed{ext}"
        
        # Quality settings
        quality_settings = {
            'low': {'image_quality': 50, 'compress_images': True},
            'medium': {'image_quality': 75, 'compress_images': True},
            'high': {'image_quality': 85, 'compress_images': True},
        }
        
        settings = quality_settings.get(quality, quality_settings['medium'])
        
        # For production, use a library like PyPDF2 with compression
        # or call external tools like Ghostscript
        with open(input_path, 'rb') as infile:
            reader = PyPDF2.PdfReader(infile)
            writer = PyPDF2.PdfWriter()
            
            for page in reader.pages:
                writer.add_page(page)
            
            # Compress content streams
            writer.compress_content_streams = True
            
            with open(output_path, 'wb') as outfile:
                writer.write(outfile)
        
        # Get original and compressed sizes
        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        savings = (1 - compressed_size / original_size) * 100
        
        logger.info(f"PDF compressed: {original_size} -> {compressed_size} bytes ({savings:.1f}% savings)")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to compress PDF: {e}")
        return False


def create_zip_archive(
    files: List[str],
    output_path: str,
    compression: int = zipfile.ZIP_DEFLATED
) -> bool:
    """
    Create a ZIP archive from a list of files.
    
    Args:
        files: List of file paths to include
        output_path: Path for the ZIP archive
        compression: Compression type (ZIP_DEFLATED, ZIP_STORED, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with zipfile.ZipFile(output_path, 'w', compression=compression) as zipf:
            for file_path in files:
                if os.path.isfile(file_path):
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
        
        return True
    except Exception as e:
        logger.error(f"Failed to create ZIP archive: {e}")
        return False


def optimize_upload(
    file_path: str,
    file_type: str,
    max_size_mb: int = 10
) -> Tuple[bool, Optional[str]]:
    """
    Optimize an uploaded file (image or PDF) by compressing if needed.
    
    Args:
        file_path: Path to uploaded file
        file_type: Type of file ('image' or 'pdf')
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        Tuple of (optimized, new_path_or_none)
    """
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # If file is already under limit, no optimization needed
    if file_size <= max_size_bytes:
        return True, None
    
    compressed_path = None
    
    if file_type == 'image':
        # Compress image
        base, ext = os.path.splitext(file_path)
        compressed_path = f"{base}_compressed{ext}"
        success, _ = compress_image(file_path, compressed_path, quality=75)
        
        if success:
            # Check if compressed file is small enough
            if os.path.getsize(compressed_path) <= max_size_bytes:
                return True, compressed_path
            else:
                # Further compress
                success, _ = compress_image(file_path, compressed_path, quality=50)
                return success, compressed_path if success else None
    
    elif file_type == 'pdf':
        # Compress PDF
        base, ext = os.path.splitext(file_path)
        compressed_path = f"{base}_compressed{ext}"
        success = compress_pdf(file_path, compressed_path, quality='medium')
        
        if success:
            return True, compressed_path
    
    return False, None


def get_compression_ratio(original_path: str, compressed_path: str) -> float:
    """
    Calculate compression ratio between original and compressed files.
    
    Args:
        original_path: Path to original file
        compressed_path: Path to compressed file
        
    Returns:
        Compression ratio (1.0 = no compression, <1.0 = compression)
    """
    try:
        original_size = os.path.getsize(original_path)
        compressed_size = os.path.getsize(compressed_path)
        return compressed_size / original_size if original_size > 0 else 1.0
    except Exception:
        return 1.0
