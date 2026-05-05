"""
Text Watermarker
================
Adds invisible watermarks to text content using Unicode characters.
"""

import hashlib
import json
from typing import Dict, Any, Optional


class TextWatermarker:
    """Adds invisible watermarks to text using zero-width characters."""
    
    # Zero-width characters for encoding
    ZWSP = '\u200B'      # Zero-width space (bit 0)
    ZWNJ = '\u200C'      # Zero-width non-joiner (bit 1)
    ZWJ = '\u200D'       # Zero-width joiner (separator)
    
    def __init__(self):
        self.separator = self.ZWJ
    
    def encode_bits(self, data: str) -> str:
        """Encode string data into bits using zero-width characters."""
        # Convert to binary representation
        binary = ''.join(format(ord(c), '016b') for c in data)
        
        # Replace 0 and 1 with zero-width characters
        result = binary.replace('0', self.ZWSP).replace('1', self.ZWNJ)
        return result
    
    def decode_bits(self, watermark: str) -> str:
        """Decode zero-width characters back to string."""
        # Replace zero-width chars back to bits
        binary = watermark.replace(self.ZWSP, '0').replace(self.ZWNJ, '1')
        
        # Remove separator if present
        binary = binary.replace(self.separator, '')
        
        # Convert bits back to string
        result = ''
        for i in range(0, len(binary), 16):
            if i + 16 <= len(binary):
                char_code = int(binary[i:i+16], 2)
                result += chr(char_code)
        
        return result
    
    def embed_watermark(self, text: str, watermark_data: Dict[str, Any]) -> str:
        """
        Embed invisible watermark into text.
        
        Args:
            text: Original text content
            watermark_data: Dictionary with watermark information
            
        Returns:
            Text with embedded watermark
        """
        # Encode watermark data as JSON
        watermark_json = json.dumps(watermark_data)
        encoded_watermark = self.encode_bits(watermark_json)
        
        # Insert watermark at beginning of text
        return encoded_watermark + self.separator + text
    
    def extract_watermark(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract invisible watermark from text.
        
        Args:
            text: Text with potential watermark
            
        Returns:
            Watermark data dictionary or None if not found
        """
        # Look for zero-width characters at the beginning
        watermark_chars = []
        for char in text:
            if char in [self.ZWSP, self.ZWNJ]:
                watermark_chars.append(char)
            else:
                break
        
        if not watermark_chars:
            return None
        
        watermark_string = ''.join(watermark_chars)
        
        # Check for separator
        if self.separator in watermark_string:
            watermark_string = watermark_string.split(self.separator)[0]
        
        try:
            decoded = self.decode_bits(watermark_string)
            return json.loads(decoded)
        except Exception:
            return None
    
    def generate_watermark_data(
        self,
        user_id: str,
        book_id: str,
        purchase_id: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """Generate watermark data for a purchase."""
        return {
            "user": user_id,
            "book": book_id,
            "purchase": purchase_id,
            "timestamp": timestamp,
            "verification": hashlib.sha256(
                f"{user_id}{book_id}{purchase_id}{timestamp}".encode()
            ).hexdigest()[:16]
        }
