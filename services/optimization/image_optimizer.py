"""
Image Optimizer
===============
Optimizes images for web delivery with compression, resizing, and format conversion.
"""

import os
from io import BytesIO
from typing import Optional, Tuple, Union
from PIL import Image
from pathlib import Path
import hashlib
from app.core.logger import logger


class ImageOptimizer:
    """Optimizes images for web delivery."""
    
    # Supported output formats
    OUTPUT_FORMATS = {
        'webp': {'quality': 80, 'lossless': False},
        'jpeg': {'quality': 85, 'progressive': True},
        'png': {'compress_level': 6},
        'avif': {'quality': 75},
    }
    
    # Size presets
    SIZE_PRESETS = {
        'thumbnail': (150, 200),    # Book thumbnails
        'small': (300, 400),        # Small display
        'medium': (600, 800),       # Medium display
        'large': (1200, 1600),      # Large display
        'hero': (1920, 1080),       # Hero images
        'cover': (400, 600),        # Book covers
    }
    
    def __init__(self, cache_dir: str = "/storage/cache/images"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, image_path: str, width: int, height: int, format: str) -> str:
        """Generate cache key for optimized image."""
        content_hash = hashlib.md5(f"{image_path}:{width}:{height}:{format}".encode()).hexdigest()
        return f"{content_hash}.{format}"
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path."""
        return self.cache_dir / cache_key
    
    def optimize(
        self,
        input_path: Union[str, bytes, BytesIO],
        output_format: str = 'webp',
        quality: Optional[int] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        preserve_ratio: bool = True
    ) -> Optional[bytes]:
        """
        Optimize an image.
        
        Args:
            input_path: Path to image or image bytes
            output_format: Output format (webp, jpeg, png, avif)
            quality: Quality setting (1-100)
            max_width: Maximum width
            max_height: Maximum height
            preserve_ratio: Maintain aspect ratio
            
        Returns:
            Optimized image bytes or None
        """
        try:
            # Load image
            if isinstance(input_path, str):
                img = Image.open(input_path)
            else:
                img = Image.open(input_path) if isinstance(input_path, BytesIO) else Image.open(BytesIO(input_path))
            
            # Convert RGBA to RGB for JPEG
            if output_format == 'jpeg' and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if dimensions specified
            if max_width or max_height:
                original_width, original_height = img.size
                
                if preserve_ratio:
                    ratio = min(
                        (max_width or original_width) / original_width,
                        (max_height or original_height) / original_height,
                        1.0
                    )
                    new_width = int(original_width * ratio)
                    new_height = int(original_height * ratio)
                else:
                    new_width = max_width or original_width
                    new_height = max_height or original_height
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Prepare save parameters
            save_kwargs = self.OUTPUT_FORMATS.get(output_format, self.OUTPUT_FORMATS['webp']).copy()
            
            if quality is not None:
                if output_format in ['webp', 'jpeg']:
                    save_kwargs['quality'] = quality
            
            # Save to bytes
            output = BytesIO()
            img.save(output, format=output_format.upper(), **save_kwargs)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return None
    
    def optimize_and_cache(
        self,
        input_path: str,
        size_preset: str = 'medium',
        output_format: str = 'webp'
    ) -> Optional[str]:
        """
        Optimize image and save to cache.
        
        Args:
            input_path: Path to source image
            size_preset: Preset size (thumbnail, small, medium, large, hero, cover)
            output_format: Output format
            
        Returns:
            Path to cached optimized image or None
        """
        if size_preset not in self.SIZE_PRESETS:
            size_preset = 'medium'
        
        width, height = self.SIZE_PRESETS[size_preset]
        cache_key = self._get_cache_key(input_path, width, height, output_format)
        cache_path = self._get_cache_path(cache_key)
        
        # Return cached version if exists
        if cache_path.exists():
            return str(cache_path)
        
        # Optimize and cache
        optimized = self.optimize(
            input_path,
            output_format=output_format,
            max_width=width,
            max_height=height
        )
        
        if optimized:
            cache_path.write_bytes(optimized)
            return str(cache_path)
        
        return None
    
    def generate_responsive_set(
        self,
        input_path: str,
        output_dir: str,
        base_name: str
    ) -> dict:
        """
        Generate responsive image set for different screen sizes.
        
        Args:
            input_path: Path to source image
            output_dir: Output directory
            base_name: Base name for output files
            
        Returns:
            Dictionary with responsive image URLs
        """
        result = {}
        
        for preset_name, (width, height) in self.SIZE_PRESETS.items():
            output_filename = f"{base_name}_{preset_name}.webp"
            output_path = os.path.join(output_dir, output_filename)
            
            optimized = self.optimize(
                input_path,
                output_format='webp',
                max_width=width,
                max_height=height
            )
            
            if optimized:
                with open(output_path, 'wb') as f:
                    f.write(optimized)
                result[preset_name] = output_filename
        
        return result
    
    def get_optimized_url(self, image_url: str, size: str = 'medium') -> str:
        """
        Generate URL for optimized image version.
        
        Args:
            image_url: Original image URL
            size: Size preset
            
        Returns:
            URL with optimization parameters (for CDN processing)
        """
        # If using a CDN that supports on-the-fly optimization
        # Example: ?w=300&h=400&fmt=webp&q=80
        sizes = self.SIZE_PRESETS.get(size, (600, 800))
        return f"{image_url}?w={sizes[0]}&h={sizes[1]}&fmt=webp&q=80"
