from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Torrent(Base):
    __tablename__ = "torrents"
    
    id = Column(Integer, primary_key=True, index=True)
    info_hash = Column(String(40), unique=True, index=True)  # SHA-1 hash (40 hex chars)
    name = Column(String, index=True)
    file_size = Column(Integer)  # Size in bytes
    piece_length = Column(Integer)  # Size of each piece in bytes
    num_pieces = Column(Integer)  # Total number of pieces
    pieces_hash = Column(LargeBinary)  # Concatenated SHA-1 hashes of all pieces
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    seeders = Column(Integer, default=0)
    leechers = Column(Integer, default=0)
    completed = Column(Integer, default=0)  # Number of completed downloads
    
    # Relationship to peers
    peers = relationship("Peer", back_populates="torrent")
    
    def __repr__(self):
        return f"<Torrent(name='{self.name}', info_hash='{self.info_hash}')>"
