"""
CDN Optimizer
=============
Manages CDN configuration and optimization for static assets.
"""

import hashlib
from typing import List, Dict, Optional
from datetime import datetime
import os
from app.core.config import settings
from app.core.logger import logger


class CDNOptimizer:
    """Optimizes content delivery through CDN configuration."""
    
    def __init__(self):
        self.cdn_url = settings.CDN_URL if settings.CDN_ENABLED else ""
        self.enabled = settings.CDN_ENABLED
    
    def get_cdn_url(self, asset_path: str, version: Optional[str] = None) -> str:
        """
        Get CDN URL for an asset with cache-busting version.
        
        Args:
            asset_path: Path to asset
            version: Optional version string for cache busting
            
        Returns:
            CDN URL
        """
        if not self.enabled or not self.cdn_url:
            return asset_path
        
        # Add version parameter for cache busting
        if version:
            separator = '&' if '?' in asset_path else '?'
            asset_path = f"{asset_path}{separator}v={version}"
        
        # Remove leading slash if present
        if asset_path.startswith('/'):
            asset_path = asset_path[1:]
        
        return f"{self.cdn_url}/{asset_path}"
    
    def get_optimized_image_url(
        self,
        image_path: str,
        width: int,
        height: int,
        format: str = 'webp',
        quality: int = 80
    ) -> str:
        """
        Get CDN URL with image optimization parameters.
        
        Args:
            image_path: Path to image
            width: Desired width
            height: Desired height
            format: Output format (webp, jpeg, png)
            quality: Image quality (1-100)
            
        Returns:
            Optimized image URL
        """
        if not self.enabled or not self.cdn_url:
            return image_path
        
        # Remove leading slash
        if image_path.startswith('/'):
            image_path = image_path[1:]
        
        # Add optimization parameters
        params = f"w={width}&h={height}&fmt={format}&q={quality}"
        return f"{self.cdn_url}/{image_path}?{params}"
    
    def generate_preconnect_tags(self) -> str:
        """
        Generate preconnect HTML tags for CDN.
        
        Returns:
            HTML link tags for CDN preconnect
        """
        if not self.enabled or not self.cdn_url:
            return ""
        
        # Extract domain from CDN URL
        domain = self.cdn_url.split('//')[1].split('/')[0]
        
        return f'<link rel="preconnect" href="{self.cdn_url}">\n<link rel="dns-prefetch" href="{self.cdn_url}">'
    
    def get_asset_version(self, asset_path: str) -> str:
        """
        Get asset version for cache busting.
        
        Args:
            asset_path: Path to asset
            
        Returns:
            Version hash or timestamp
        """
        # In production, use file modification time or content hash
        try:
            if os.path.exists(asset_path):
                mtime = os.path.getmtime(asset_path)
                return str(int(mtime))
        except Exception as exc:
            logger.debug(f"Failed to get asset mtime for versioning: path={asset_path}, error={exc}")
        
        return str(datetime.utcnow().timestamp())[:10]
    
    def get_critical_css_inline(self) -> str:
        """
        Get critical CSS to inline for above-the-fold content.
        
        Returns:
            Critical CSS string
        """
        # Critical CSS for above-the-fold content
        return """
        /* Critical CSS for above-the-fold content */
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.6;color:#1a1a1a}
        .container{max-width:1200px;margin:0 auto;padding:0 1rem}
        .btn{display:inline-block;padding:0.75rem 1.5rem;border-radius:0.5rem;text-decoration:none;font-weight:500;transition:all 0.3s}
        .btn-primary{background:#6366f1;color:white}
        .site-header{background:white;box-shadow:0 1px 2px rgba(0,0,0,0.05);position:sticky;top:0;z-index:1000}
        """
    
    def should_use_cdn(self, asset_path: str) -> bool:
        """
        Determine if an asset should be served from CDN.
        
        Args:
            asset_path: Path to asset
            
        Returns:
            True if asset should use CDN
        """
        # Static assets that benefit from CDN
        cdn_extensions = ['.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.woff', '.woff2']
        return self.enabled and any(asset_path.lower().endswith(ext) for ext in cdn_extensions)
