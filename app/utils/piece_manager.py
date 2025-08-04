from typing import List, Dict, Set
import threading
import time

class PieceManager:
    """Manages piece tracking and availability for torrents"""
    
    def __init__(self, total_pieces: int):
        self.total_pieces = total_pieces
        self.completed_pieces: Set[int] = set()
        self.requested_pieces: Set[int] = set()
        self.piece_availability: Dict[int, int] = {}  # piece_index -> number of peers who have it
        self.lock = threading.Lock()
    
    def mark_piece_completed(self, piece_index: int) -> None:
        """Mark a piece as completed"""
        with self.lock:
            self.completed_pieces.add(piece_index)
            if piece_index in self.requested_pieces:
                self.requested_pieces.remove(piece_index)
    
    def mark_piece_requested(self, piece_index: int) -> None:
        """Mark a piece as currently being requested"""
        with self.lock:
            if piece_index not in self.completed_pieces:
                self.requested_pieces.add(piece_index)
    
    def get_next_piece_to_request(self) -> int:
        """Get the next piece to request (rarest first strategy)"""
        with self.lock:
            available_pieces = []
            
            for piece_index in range(self.total_pieces):
                if (piece_index not in self.completed_pieces and 
                    piece_index not in self.requested_pieces and
                    piece_index in self.piece_availability):
                    available_pieces.append(piece_index)
            
            if not available_pieces:
                return -1  # No pieces available
            
            # Sort by rarity (rarest first)
            available_pieces.sort(key=lambda x: self.piece_availability[x])
            return available_pieces[0]
    
    def update_peer_pieces(self, peer_id: str, pieces: List[int]) -> None:
        """Update which pieces a peer has"""
        with self.lock:
            # Reset availability count
            for piece_index in pieces:
                if piece_index not in self.piece_availability:
                    self.piece_availability[piece_index] = 0
                self.piece_availability[piece_index] += 1
    
    def get_completion_percentage(self) -> float:
        """Get download completion percentage"""
        with self.lock:
            if self.total_pieces == 0:
                return 100.0
            return (len(self.completed_pieces) / self.total_pieces) * 100.0
    
    def is_complete(self) -> bool:
        """Check if all pieces are downloaded"""
        with self.lock:
            return len(self.completed_pieces) == self.total_pieces
    
    def get_missing_pieces(self) -> List[int]:
        """Get list of missing piece indices"""
        with self.lock:
            missing = []
            for i in range(self.total_pieces):
                if i not in self.completed_pieces:
                    missing.append(i)
            return missing
