"""
Image Watermarker
=================
Adds visible and invisible watermarks to cover images.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import hashlib
from typing import Optional, Tuple
from io import BytesIO
import base64


class ImageWatermarker:
    """Adds watermarks to book cover images."""
    
    def __init__(self):
        self.font_path = "/app/assets/fonts/Inter-Regular.ttf"
        self.watermark_opacity = 0.3
        self.position = "bottom_right"
    
    def add_text_watermark(
        self,
        image_path: str,
        output_path: str,
        text: str,
        position: str = "bottom_right",
        opacity: float = 0.3
    ) -> bool:
        """
        Add visible text watermark to image.
        
        Args:
            image_path: Path to source image
            output_path: Path for watermarked image
            text: Watermark text
            position: Watermark position (bottom_right, bottom_left, center)
            opacity: Watermark opacity (0-1)
            
        Returns:
            True if successful
        """
        try:
            # Open image
            img = Image.open(image_path).convert("RGBA")
            
            # Create watermark layer
            watermark = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Try to load font
            try:
                font_size = min(img.width, img.height) // 20
                font = ImageFont.truetype(self.font_path, font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text size and position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if position == "bottom_right":
                x = img.width - text_width - 20
                y = img.height - text_height - 20
            elif position == "bottom_left":
                x = 20
                y = img.height - text_height - 20
            elif position == "center":
                x = (img.width - text_width) // 2
                y = (img.height - text_height) // 2
            else:
                x = img.width - text_width - 20
                y = img.height - text_height - 20
            
            # Draw watermark
            draw.text((x, y), text, fill=(255, 255, 255, int(255 * opacity)), font=font)
            
            # Composite and save
            watermarked = Image.alpha_composite(img, watermark)
            watermarked.convert("RGB").save(output_path, "JPEG", quality=85)
            
            return True
            
        except Exception as e:
            print(f"Failed to add watermark: {e}")
            return False
    
    def add_invisible_watermark(
        self,
        image_path: str,
        output_path: str,
        data: str
    ) -> bool:
        """
        Add invisible watermark using LSB steganography.
        
        Args:
            image_path: Path to source image
            output_path: Path for watermarked image
            data: Data to embed
            
        Returns:
            True if successful
        """
        try:
            img = Image.open(image_path)
            pixels = img.load()
            
            # Convert data to binary
            binary_data = ''.join(format(ord(c), '08b') for c in data) + '1111111111111110'  # End marker
            
            width, height = img.size
            data_index = 0
            
            # Embed data in least significant bits
            for y in range(height):
                for x in range(width):
                    if data_index < len(binary_data):
                        pixel = list(pixels[x, y])
                        for c in range(3):  # RGB channels
                            if data_index < len(binary_data):
                                pixel[c] = (pixel[c] & 0xFE) | int(binary_data[data_index])
                                data_index += 1
                        pixels[x, y] = tuple(pixel)
                    else:
                        break
                if data_index >= len(binary_data):
                    break
            
            img.save(output_path, "PNG")
            return True
            
        except Exception as e:
            print(f"Failed to add invisible watermark: {e}")
            return False
    
    def extract_invisible_watermark(self, image_path: str) -> Optional[str]:
        """
        Extract invisible watermark from image.
        
        Args:
            image_path: Path to watermarked image
            
        Returns:
            Extracted data or None
        """
        try:
            img = Image.open(image_path)
            pixels = img.load()
            
            binary_data = ""
            width, height = img.size
            
            for y in range(height):
                for x in range(width):
                    pixel = pixels[x, y]
                    for c in range(3):
                        binary_data += str(pixel[c] & 1)
            
            # Find end marker
            end_marker = '1111111111111110'
            marker_pos = binary_data.find(end_marker)
            
            if marker_pos > 0:
                binary_data = binary_data[:marker_pos]
                
                # Convert binary to text
                text = ''
                for i in range(0, len(binary_data), 8):
                    if i + 8 <= len(binary_data):
                        byte = binary_data[i:i+8]
                        text += chr(int(byte, 2))
                
                return text
            
            return None
            
        except Exception as e:
            print(f"Failed to extract watermark: {e}")
            return None
