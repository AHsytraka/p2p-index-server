from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Peer(Base):
    __tablename__ = "peers"
    
    id = Column(Integer, primary_key=True, index=True)
    peer_id = Column(String(20), unique=True, index=True)  # Unique peer identifier
    ip_address = Column(String(15), index=True)  # IPv4 address
    port = Column(Integer, index=True)
    torrent_id = Column(Integer, ForeignKey("torrents.id"))
    uploaded = Column(Integer, default=0)  # Bytes uploaded
    downloaded = Column(Integer, default=0)  # Bytes downloaded
    left = Column(Integer, default=0)  # Bytes left to download
    is_seeder = Column(Boolean, default=False)
    last_announce = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to torrent
    torrent = relationship("Torrent", back_populates="peers")
    
    def __repr__(self):
        return f"<Peer(peer_id='{self.peer_id}', ip='{self.ip_address}', port={self.port})>"
