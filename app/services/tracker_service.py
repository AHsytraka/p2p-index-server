from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.torrent import Torrent
from app.models.peer import Peer
from app.models.user import User
from app.schemas.torrent import TorrentCreate, TorrentResponse, TorrentAnnounceRequest
from app.schemas.peer import PeerResponse, PeerListResponse
from app.schemas.user import UserCreate, UserResponse
from app.utils.bittorrent import BitTorrentUtils

class TrackerService:
    def __init__(self, db: Session):
        self.db = db
    
    # Torrent management
    def create_torrent(self, torrent_data: TorrentCreate) -> TorrentResponse:
        """Create a new torrent in the tracker"""
        # Check if torrent already exists
        existing = self.db.query(Torrent).filter(Torrent.info_hash == torrent_data.info_hash).first()
        if existing:
            # Return existing torrent instead of raising an error
            return TorrentResponse.from_orm(existing)
        
        torrent = Torrent(
            info_hash=torrent_data.info_hash,
            name=torrent_data.name,
            file_size=torrent_data.file_size,
            piece_length=torrent_data.piece_length,
            num_pieces=torrent_data.num_pieces,
            pieces_hash=torrent_data.pieces_hash
        )
        
        self.db.add(torrent)
        self.db.commit()
        self.db.refresh(torrent)
        
        return TorrentResponse.from_orm(torrent)
    
    def get_torrent(self, info_hash: str) -> Optional[TorrentResponse]:
        """Get torrent by info hash"""
        torrent = self.db.query(Torrent).filter(Torrent.info_hash == info_hash).first()
        if torrent:
            return TorrentResponse.from_orm(torrent)
        return None
    
    def list_torrents(self, limit: int = 100) -> List[TorrentResponse]:
        """List all torrents"""
        torrents = self.db.query(Torrent).limit(limit).all()
        return [TorrentResponse.from_orm(t) for t in torrents]
    
    # Peer announce and tracking
    def announce(self, announce_data: TorrentAnnounceRequest, client_ip: str) -> PeerListResponse:
        """Handle peer announce request"""
        # Validate info hash
        if not BitTorrentUtils.validate_info_hash(announce_data.info_hash):
            raise HTTPException(status_code=400, detail="Invalid info hash")
        
        # Validate peer ID
        if not BitTorrentUtils.validate_peer_id(announce_data.peer_id):
            raise HTTPException(status_code=400, detail="Invalid peer ID")
        
        # Get torrent
        torrent = self.db.query(Torrent).filter(Torrent.info_hash == announce_data.info_hash).first()
        if not torrent:
            raise HTTPException(status_code=404, detail="Torrent not found")
        
        # Use provided IP or client IP
        peer_ip = announce_data.ip or client_ip
        
        # Find or create peer
        peer = self.db.query(Peer).filter(
            and_(
                Peer.peer_id == announce_data.peer_id,
                Peer.torrent_id == torrent.id
            )
        ).first()
        
        if not peer:
            peer = Peer(
                peer_id=announce_data.peer_id,
                ip_address=peer_ip,
                port=announce_data.port,
                torrent_id=torrent.id
            )
            self.db.add(peer)
        
        # Update peer information
        peer.ip_address = peer_ip
        peer.port = announce_data.port
        peer.uploaded = announce_data.uploaded
        peer.downloaded = announce_data.downloaded
        peer.left = announce_data.left
        peer.is_seeder = announce_data.left == 0
        peer.last_announce = datetime.utcnow()
        
        # Handle events
        if announce_data.event == "completed":
            torrent.completed += 1
        elif announce_data.event == "stopped":
            self.db.delete(peer)
            self.db.commit()
            return PeerListResponse(peers=[])
        
        self.db.commit()
        
        # Update torrent stats
        self._update_torrent_stats(torrent.id)
        
        # Get peer list (excluding the announcing peer)
        peers = self.db.query(Peer).filter(
            and_(
                Peer.torrent_id == torrent.id,
                Peer.peer_id != announce_data.peer_id,
                Peer.last_announce > datetime.utcnow() - timedelta(hours=2)  # Active peers
            )
        ).limit(50).all()  # Limit to 50 peers
        
        peer_responses = [PeerResponse.from_orm(p) for p in peers]
        
        return PeerListResponse(peers=peer_responses, interval=1800)  # 30 minutes
    
    def _update_torrent_stats(self, torrent_id: int):
        """Update torrent seeder/leecher counts"""
        torrent = self.db.query(Torrent).filter(Torrent.id == torrent_id).first()
        if not torrent:
            return
        
        active_cutoff = datetime.utcnow() - timedelta(hours=2)
        
        seeders = self.db.query(Peer).filter(
            and_(
                Peer.torrent_id == torrent_id,
                Peer.is_seeder == True,
                Peer.last_announce > active_cutoff
            )
        ).count()
        
        leechers = self.db.query(Peer).filter(
            and_(
                Peer.torrent_id == torrent_id,
                Peer.is_seeder == False,
                Peer.last_announce > active_cutoff
            )
        ).count()
        
        torrent.seeders = seeders
        torrent.leechers = leechers
        self.db.commit()
    
    def get_peers(self, info_hash: str) -> List[PeerResponse]:
        """Get active peers for a torrent"""
        torrent = self.db.query(Torrent).filter(Torrent.info_hash == info_hash).first()
        if not torrent:
            raise HTTPException(status_code=404, detail="Torrent not found")
        
        active_cutoff = datetime.utcnow() - timedelta(hours=2)
        peers = self.db.query(Peer).filter(
            and_(
                Peer.torrent_id == torrent.id,
                Peer.last_announce > active_cutoff
            )
        ).all()
        
        return [PeerResponse.from_orm(p) for p in peers]
    
    # User management
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        # Check if username already exists
        existing = self.db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Generate peer ID for user
        peer_id = BitTorrentUtils.generate_peer_id()
        
        user = User(
            username=user_data.username,
            peer_id=peer_id
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse.from_orm(user)
    
    def get_user_by_peer_id(self, peer_id: str) -> Optional[UserResponse]:
        """Get user by peer ID"""
        user = self.db.query(User).filter(User.peer_id == peer_id).first()
        if user:
            return UserResponse.from_orm(user)
        return None
    
    # Statistics
    def get_tracker_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        total_torrents = self.db.query(Torrent).count()
        total_peers = self.db.query(Peer).count()
        total_users = self.db.query(User).count()
        
        active_cutoff = datetime.utcnow() - timedelta(hours=2)
        active_peers = self.db.query(Peer).filter(Peer.last_announce > active_cutoff).count()
        
        return {
            'total_torrents': total_torrents,
            'total_peers': total_peers,
            'active_peers': active_peers,
            'total_users': total_users
        }
    
    def cleanup_localhost_peers(self) -> int:
        """Remove all localhost (127.0.0.1) peers"""
        count = self.db.query(Peer).filter(Peer.ip_address == "127.0.0.1").count()
        self.db.query(Peer).filter(Peer.ip_address == "127.0.0.1").delete()
        self.db.commit()
        return count
    
    def deduplicate_peers(self) -> int:
        """Remove duplicate peers (same IP:port for same torrent, keep the most recent)"""
        # Get all peers grouped by IP, port, and torrent
        from sqlalchemy import func
        
        subquery = self.db.query(
            Peer.ip_address,
            Peer.port,
            Peer.torrent_id,
            func.max(Peer.last_announce).label('max_announce')
        ).group_by(
            Peer.ip_address,
            Peer.port,
            Peer.torrent_id
        ).subquery()
        
        # Get peers to keep (most recent for each IP:port:torrent combination)
        peers_to_keep = self.db.query(Peer.id).join(
            subquery,
            and_(
                Peer.ip_address == subquery.c.ip_address,
                Peer.port == subquery.c.port,
                Peer.torrent_id == subquery.c.torrent_id,
                Peer.last_announce == subquery.c.max_announce
            )
        ).all()
        
        keep_ids = [p.id for p in peers_to_keep]
        
        # Count duplicates to be removed
        if keep_ids:
            count = self.db.query(Peer).filter(~Peer.id.in_(keep_ids)).count()
            # Remove duplicates
            self.db.query(Peer).filter(~Peer.id.in_(keep_ids)).delete(synchronize_session=False)
        else:
            count = 0
            
        self.db.commit()
        return count