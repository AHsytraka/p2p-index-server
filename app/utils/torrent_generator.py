import hashlib
import os
import json
from typing import Dict, Any, List

class TorrentGenerator:
    """Handles torrent file generation and metadata creation"""
    
    DEFAULT_PIECE_LENGTH = 2**18  # 256KB
    
    @staticmethod
    def calculate_piece_hashes(file_path: str, piece_length: int = DEFAULT_PIECE_LENGTH) -> List[bytes]:
        """Calculate SHA-1 hash for each piece of the file"""
        piece_hashes = []
        
        with open(file_path, 'rb') as f:
            while True:
                piece_data = f.read(piece_length)
                if not piece_data:
                    break
                
                piece_hash = hashlib.sha1(piece_data).digest()
                piece_hashes.append(piece_hash)
        
        return piece_hashes
    
    @staticmethod
    def calculate_info_hash(torrent_info: Dict[str, Any]) -> str:
        """Calculate the info hash (SHA-1 of the info section)"""
        # Sort keys to ensure consistent hash
        info_str = json.dumps(torrent_info, sort_keys=True, separators=(',', ':'))
        return hashlib.sha1(info_str.encode('utf-8')).hexdigest()
    
    @classmethod
    def create_torrent_metadata(cls, file_path: str, tracker_url: str, 
                              piece_length: int = DEFAULT_PIECE_LENGTH) -> Dict[str, Any]:
        """Create torrent metadata dictionary"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        # Calculate piece hashes
        piece_hashes = cls.calculate_piece_hashes(file_path, piece_length)
        pieces_hash = b''.join(piece_hashes)
        
        # Create info section
        info = {
            'name': file_name,
            'length': file_size,
            'piece length': piece_length,
            'pieces': pieces_hash.hex()  # Store as hex string for JSON compatibility
        }
        
        # Calculate info hash
        info_hash = cls.calculate_info_hash(info)
        
        # Create complete torrent metadata
        torrent_data = {
            'announce': tracker_url,
            'info': info,
            'info_hash': info_hash,
            'creation date': int(os.path.getctime(file_path)),
            'created by': 'P2P-BitTorrent-Python',
            'comment': f'Generated torrent for {file_name}'
        }
        
        return torrent_data
    
    @staticmethod
    def save_torrent_file(torrent_data: Dict[str, Any], output_path: str = None) -> str:
        """Save torrent metadata to a .torrent file (JSON format)"""
        if output_path is None:
            # Create a proper filename based on the original file name
            original_name = torrent_data['info']['name']
            # Remove file extension and add .torrent
            base_name = os.path.splitext(original_name)[0]
            torrent_filename = f"{base_name}.torrent"
        else:
            torrent_filename = output_path
            if not torrent_filename.endswith('.torrent'):
                torrent_filename += '.torrent'
        
        # Ensure the directory exists
        output_dir = os.path.dirname(torrent_filename) if os.path.dirname(torrent_filename) else '.'
        os.makedirs(output_dir, exist_ok=True)
        
        with open(torrent_filename, 'w', encoding='utf-8') as f:
            json.dump(torrent_data, f, indent=2, ensure_ascii=False)
        
        return torrent_filename
    
    @staticmethod
    def load_torrent_file(torrent_path: str) -> Dict[str, Any]:
        """Load torrent metadata from a .torrent file"""
        with open(torrent_path, 'r', encoding='utf-8') as f:
            return json.load(f)
