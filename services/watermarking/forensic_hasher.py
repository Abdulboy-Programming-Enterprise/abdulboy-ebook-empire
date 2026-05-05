"""
Forensic Hasher
===============
Generates cryptographic hashes for content verification and tamper detection.
"""

import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime


class ForensicHasher:
    """Generates and verifies cryptographic hashes for ebooks."""
    
    def __init__(self):
        self.algorithm = "sha256"
    
    def generate_content_hash(self, content: bytes) -> str:
        """
        Generate SHA-256 hash of content.
        
        Args:
            content: Content bytes
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content).hexdigest()
    
    def generate_file_hash(self, file_path: str, chunk_size: int = 8192) -> Optional[str]:
        """
        Generate hash of file contents.
        
        Args:
            file_path: Path to file
            chunk_size: Read chunk size
            
        Returns:
            Hexadecimal hash string or None
        """
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return None
    
    def generate_watermark_hash(
        self,
        user_id: str,
        book_id: str,
        purchase_id: str,
        timestamp: str,
        salt: str = "ABDULBOY_SEED_2026"
    ) -> str:
        """
        Generate a forensic hash for watermark verification.
        
        Args:
            user_id: User identifier
            book_id: Book identifier
            purchase_id: Purchase identifier
            timestamp: ISO timestamp
            salt: Secret salt for hash
            
        Returns:
            Forensic hash string
        """
        data = f"{user_id}:{book_id}:{purchase_id}:{timestamp}:{salt}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def verify_watermark(
        self,
        user_id: str,
        book_id: str,
        purchase_id: str,
        timestamp: str,
        provided_hash: str
    ) -> bool:
        """
        Verify a watermark hash.
        
        Args:
            user_id: User identifier
            book_id: Book identifier
            purchase_id: Purchase identifier
            timestamp: ISO timestamp
            provided_hash: Hash to verify
            
        Returns:
            True if hash is valid
        """
        expected_hash = self.generate_watermark_hash(
            user_id, book_id, purchase_id, timestamp
        )
        return expected_hash == provided_hash
    
    def generate_fingerprint(self, metadata: Dict[str, Any]) -> str:
        """
        Generate a unique fingerprint for a document.
        
        Args:
            metadata: Document metadata dictionary
            
        Returns:
            Fingerprint hash
        """
        # Normalize metadata
        fingerprint_data = {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "isbn": metadata.get("isbn", ""),
            "page_count": metadata.get("page_count", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return hashlib.sha256(
            json.dumps(fingerprint_data, sort_keys=True).encode()
        ).hexdigest()
    
    def create_verification_report(
        self,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a verification report for a file.
        
        Args:
            file_path: Path to file
            metadata: File metadata
            
        Returns:
            Verification report dictionary
        """
        return {
            "file_hash": self.generate_file_hash(file_path),
            "fingerprint": self.generate_fingerprint(metadata),
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat(),
            "algorithm": self.algorithm
        }
