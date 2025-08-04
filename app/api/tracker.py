from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request, UploadFile, File, Form
from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
import tempfile
import os

from app.db.session import get_db
from app.services.tracker_service import TrackerService
from app.schemas.torrent import TorrentCreate, TorrentResponse, TorrentAnnounceRequest
from app.schemas.peer import PeerResponse, PeerListResponse
from app.schemas.user import UserCreate, UserResponse
from app.utils.torrent_generator import TorrentGenerator
from app.utils.file_manager import FileManager

router = APIRouter()

# Dependency injection
def get_tracker_service(db: Session = Depends(get_db)):
    return TrackerService(db)

# Torrent management endpoints
@router.post("/upload", response_model=TorrentResponse)
async def upload_file_and_create_torrent(
    file: UploadFile = File(...),
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Upload a file and create a torrent for it"""
    try:
        # Create directories for file storage
        upload_dir = "uploads"
        torrent_dir = "torrents"
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(torrent_dir, exist_ok=True)
        
        # Save uploaded file with proper naming
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Create a safe filename
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in (' ', '-', '_', '.'))
        if not safe_filename or safe_filename.strip() == "":
            safe_filename = "uploaded_file"
        
        uploaded_file_path = os.path.join(upload_dir, safe_filename)
        
        # Handle duplicate filenames
        counter = 1
        original_path = uploaded_file_path
        while os.path.exists(uploaded_file_path):
            name_part = os.path.splitext(original_path)[0]
            ext_part = os.path.splitext(original_path)[1]
            uploaded_file_path = f"{name_part}_{counter}{ext_part}"
            counter += 1
        
        # Save the uploaded file
        with open(uploaded_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Generate torrent metadata
            tracker_url = "http://localhost:8000/api/tracker/announce"  # This should be configurable
            torrent_data = TorrentGenerator.create_torrent_metadata(
                uploaded_file_path, 
                tracker_url
            )
            
            # Update the torrent name to use the original filename
            torrent_data['info']['name'] = safe_filename
            
            # Convert pieces hash from hex string to bytes
            pieces_hash_bytes = bytes.fromhex(torrent_data['info']['pieces'])
            
            # Create torrent in database
            torrent_create = TorrentCreate(
                name=torrent_data['info']['name'],
                file_size=torrent_data['info']['length'],
                piece_length=torrent_data['info']['piece length'],
                info_hash=torrent_data['info_hash'],
                num_pieces=len(pieces_hash_bytes) // 20,  # Each SHA-1 hash is 20 bytes
                pieces_hash=pieces_hash_bytes
            )
            
            result = tracker_service.create_torrent(torrent_create)
            
            # Save the .torrent file in the torrents directory
            torrent_filename = os.path.join(torrent_dir, f"{os.path.splitext(safe_filename)[0]}.torrent")
            TorrentGenerator.save_torrent_file(torrent_data, torrent_filename)
            
            return result
            
        except HTTPException as he:
            # Clean up uploaded file if torrent creation fails
            if os.path.exists(uploaded_file_path):
                os.unlink(uploaded_file_path)
            raise he  # Re-raise HTTP exceptions as-is
        except Exception as e:
            # Clean up uploaded file if torrent creation fails
            if os.path.exists(uploaded_file_path):
                os.unlink(uploaded_file_path)
            raise e
            
    except Exception as e:
        # Clean up uploaded file if it exists
        if 'uploaded_file_path' in locals() and os.path.exists(uploaded_file_path):
            try:
                os.unlink(uploaded_file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Failed to create torrent: {str(e)}")

@router.post("/torrents", response_model=TorrentResponse)
def create_torrent(
    torrent_data: TorrentCreate,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Create a new torrent entry"""
    return tracker_service.create_torrent(torrent_data)

@router.get("/torrents", response_model=List[TorrentResponse])
def list_torrents(
    limit: int = 100,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """List all torrents"""
    return tracker_service.list_torrents(limit)

@router.get("/torrents/{info_hash}", response_model=TorrentResponse)
def get_torrent(
    info_hash: str,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Get torrent by info hash"""
    torrent = tracker_service.get_torrent(info_hash)
    if not torrent:
        raise HTTPException(status_code=404, detail="Torrent not found")
    return torrent

@router.get("/torrents/{info_hash}/download")
def download_torrent_file(
    info_hash: str,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Download the .torrent file for a specific torrent"""
    torrent = tracker_service.get_torrent(info_hash)
    if not torrent:
        raise HTTPException(status_code=404, detail="Torrent not found")
    
    # Construct the torrent file path
    torrent_filename = f"{os.path.splitext(torrent.name)[0]}.torrent"
    torrent_file_path = os.path.join("torrents", torrent_filename)
    
    # Check if the torrent file exists
    if not os.path.exists(torrent_file_path):
        # If not found, try to regenerate it
        try:
            # Create torrent metadata
            tracker_url = "http://localhost:8000/api/tracker/announce"
            uploaded_file_path = os.path.join("uploads", torrent.name)
            
            if os.path.exists(uploaded_file_path):
                torrent_data = TorrentGenerator.create_torrent_metadata(
                    uploaded_file_path, 
                    tracker_url
                )
                os.makedirs("torrents", exist_ok=True)
                TorrentGenerator.save_torrent_file(torrent_data, torrent_file_path)
            else:
                raise HTTPException(status_code=404, detail="Original file not found, cannot regenerate torrent")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to regenerate torrent file: {str(e)}")
    
    return FileResponse(
        path=torrent_file_path,
        filename=torrent_filename,
        media_type='application/x-bittorrent'
    )

# Peer tracking endpoints
@router.get("/announce", response_model=PeerListResponse)
@router.post("/announce", response_model=PeerListResponse)
def announce(
    request: Request,
    info_hash: str,
    peer_id: str,
    port: int,
    uploaded: int = 0,
    downloaded: int = 0,
    left: int = 0,
    event: Optional[str] = None,
    ip: Optional[str] = None,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Handle peer announce requests (both GET and POST)"""
    # Get client IP
    client_ip = request.client.host
    
    announce_data = TorrentAnnounceRequest(
        info_hash=info_hash,
        peer_id=peer_id,
        ip=ip,
        port=port,
        uploaded=uploaded,
        downloaded=downloaded,
        left=left,
        event=event
    )
    
    return tracker_service.announce(announce_data, client_ip)

@router.get("/peers/{info_hash}", response_model=List[PeerResponse])
def get_peers(
    info_hash: str,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Get active peers for a torrent"""
    return tracker_service.get_peers(info_hash)

# User management endpoints
@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Create a new user"""
    return tracker_service.create_user(user_data)

@router.get("/users/{peer_id}", response_model=UserResponse)
def get_user_by_peer_id(
    peer_id: str,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Get user by peer ID"""
    user = tracker_service.get_user_by_peer_id(peer_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Statistics endpoint
@router.get("/stats")
def get_tracker_stats(
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Get tracker statistics"""
    return tracker_service.get_tracker_stats()
