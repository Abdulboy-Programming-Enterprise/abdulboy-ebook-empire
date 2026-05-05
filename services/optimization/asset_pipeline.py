"""
Asset Pipeline
==============
Minifies and bundles CSS and JavaScript assets.
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess
import json
from app.core.logger import logger


class AssetPipeline:
    """Manages CSS/JS asset minification and bundling."""
    
    def __init__(self, static_dir: str = "/app/static", build_dir: str = "/app/static/build"):
        self.static_dir = Path(static_dir)
        self.build_dir = Path(build_dir)
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> dict:
        """Load asset manifest if exists."""
        manifest_path = self.build_dir / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_manifest(self):
        """Save asset manifest."""
        manifest_path = self.build_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def minify_css(self, css_content: str) -> str:
        """
        Minify CSS content.
        
        Args:
            css_content: Raw CSS string
            
        Returns:
            Minified CSS
        """
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r'\s*([{}:;,])\s*', r'\1', css_content)
        css_content = re.sub(r';}', '}', css_content)
        css_content = re.sub(r'^\s+|\s+$', '', css_content)
        
        return css_content
    
    def minify_js(self, js_content: str) -> str:
        """
        Minify JavaScript content.
        
        Args:
            js_content: Raw JavaScript string
            
        Returns:
            Minified JavaScript
        """
        # Remove single-line comments
        js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
        
        # Remove multi-line comments
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # Remove whitespace
        js_content = re.sub(r'\s+', ' ', js_content)
        js_content = re.sub(r'\s*([{}()\[\]=;:,<>+-/*])\s*', r'\1', js_content)
        
        # Remove trailing semicolons where safe
        js_content = re.sub(r';}', '}', js_content)
        
        return js_content.strip()
    
    def bundle_css(self, files: List[str], output_name: str = "app") -> bool:
        """
        Bundle multiple CSS files into one minified file.
        
        Args:
            files: List of CSS file paths
            output_name: Output bundle name
            
        Returns:
            True if successful
        """
        try:
            combined = []
            for file_path in files:
                full_path = self.static_dir / file_path
                if full_path.exists():
                    with open(full_path, 'r') as f:
                        combined.append(f.read())
                else:
                    logger.warning(f"CSS file not found: {file_path}")
            
            minified = self.minify_css('\n'.join(combined))
            
            output_path = self.build_dir / f"{output_name}.min.css"
            with open(output_path, 'w') as f:
                f.write(minified)
            
            self.manifest[f"{output_name}.css"] = f"{output_name}.min.css"
            self._save_manifest()
            
            logger.info(f"CSS bundle created: {output_name}.min.css")
            return True
            
        except Exception as e:
            logger.error(f"CSS bundling failed: {e}")
            return False
    
    def bundle_js(self, files: List[str], output_name: str = "app") -> bool:
        """
        Bundle multiple JS files into one minified file.
        
        Args:
            files: List of JS file paths
            output_name: Output bundle name
            
        Returns:
            True if successful
        """
        try:
            combined = []
            for file_path in files:
                full_path = self.static_dir / file_path
                if full_path.exists():
                    with open(full_path, 'r') as f:
                        combined.append(f.read())
                else:
                    logger.warning(f"JS file not found: {file_path}")
            
            minified = self.minify_js('\n'.join(combined))
            
            output_path = self.build_dir / f"{output_name}.min.js"
            with open(output_path, 'w') as f:
                f.write(minified)
            
            self.manifest[f"{output_name}.js"] = f"{output_name}.min.js"
            self._save_manifest()
            
            logger.info(f"JS bundle created: {output_name}.min.js")
            return True
            
        except Exception as e:
            logger.error(f"JS bundling failed: {e}")
            return False
    
    def get_asset_url(self, asset_name: str) -> str:
        """
        Get optimized asset URL.
        
        Args:
            asset_name: Original asset name
            
        Returns:
            URL to minified asset
        """
        if asset_name in self.manifest:
            return f"/static/build/{self.manifest[asset_name]}"
        return f"/static/{asset_name}"
    
    def clean_build(self):
        """Clean build directory."""
        for file in self.build_dir.iterdir():
            if file.name != "manifest.json":
                file.unlink()
        self.manifest = {}
        self._save_manifest()
        logger.info("Build directory cleaned")
