from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TorrentBase(BaseModel):
    name: str
    file_size: int
    piece_length: int

class TorrentCreate(TorrentBase):
    info_hash: str
    num_pieces: int
    pieces_hash: bytes

class TorrentResponse(TorrentBase):
    id: int
    info_hash: str
    num_pieces: int
    created_at: datetime
    seeders: int
    leechers: int
    completed: int
    
    class Config:
        from_attributes = True

class TorrentAnnounceRequest(BaseModel):
    info_hash: str
    peer_id: str
    ip: Optional[str] = None
    port: int
    uploaded: int = 0
    downloaded: int = 0
    left: int = 0
    event: Optional[str] = None  # 'started', 'stopped', 'completed'
