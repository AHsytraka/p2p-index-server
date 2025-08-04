from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PeerBase(BaseModel):
    peer_id: str
    ip_address: str
    port: int

class PeerCreate(PeerBase):
    torrent_id: int
    uploaded: int = 0
    downloaded: int = 0
    left: int = 0

class PeerResponse(PeerBase):
    id: int
    torrent_id: int
    uploaded: int
    downloaded: int
    left: int
    is_seeder: bool
    last_announce: datetime
    
    class Config:
        from_attributes = True

class PeerListResponse(BaseModel):
    peers: list[PeerResponse]
    interval: int = 1800  # Announce interval in seconds (30 minutes)
