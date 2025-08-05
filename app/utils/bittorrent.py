import hashlib
import random
import string
from typing import Dict, Any

class BitTorrentUtils:
    """Utility functions for BitTorrent protocol"""
    
    @staticmethod
    def generate_peer_id(prefix: str = "P2PY", info_hash: str = None, ip_address: str = None) -> str:
        """Generate a consistent peer ID based on device and torrent"""
        if info_hash and ip_address:
            # Generate consistent peer ID based on IP, prefix, and info_hash
            hash_input = f"{prefix}_{ip_address}_{info_hash}".encode()
            hash_result = hashlib.md5(hash_input).hexdigest()[:16]
            return f"{prefix}{hash_result}"[:20]  # Ensure 20 chars max
        else:
            # Fallback to random if no info provided
            random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            return f"{prefix}{random_part}"[:20]  # Ensure 20 chars max
    
    @staticmethod
    def calculate_sha1(data: bytes) -> str:
        """Calculate SHA-1 hash of data"""
        return hashlib.sha1(data).hexdigest()
    
    @staticmethod
    def validate_info_hash(info_hash: str) -> bool:
        """Validate info hash format (40 hex characters)"""
        if len(info_hash) != 40:
            return False
        try:
            int(info_hash, 16)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_peer_id(peer_id: str) -> bool:
        """Validate peer ID format (20 characters max)"""
        return len(peer_id) <= 20
    
    @staticmethod
    def format_bytes(bytes_count: int) -> str:
        """Format bytes count to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    @staticmethod
    def format_speed(bytes_per_second: float) -> str:
        """Format speed to human readable format"""
        return f"{BitTorrentUtils.format_bytes(int(bytes_per_second))}/s"
    
    @staticmethod
    def calculate_eta(bytes_left: int, bytes_per_second: float) -> str:
        """Calculate estimated time of arrival"""
        if bytes_per_second <= 0:
            return "∞"
        
        seconds_left = bytes_left / bytes_per_second
        
        if seconds_left < 60:
            return f"{int(seconds_left)}s"
        elif seconds_left < 3600:
            return f"{int(seconds_left // 60)}m {int(seconds_left % 60)}s"
        else:
            hours = int(seconds_left // 3600)
            minutes = int((seconds_left % 3600) // 60)
            return f"{hours}h {minutes}m"
