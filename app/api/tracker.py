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
from app.utils.bittorrent import BitTorrentUtils
from app.services.auto_seeder_service import auto_seeder_manager

router = APIRouter()

# Dependency injection
def get_tracker_service(db: Session = Depends(get_db)):
    return TrackerService(db)

# Torrent management endpoints
@router.post("/upload", response_model=TorrentResponse)
async def upload_file_and_create_torrent(
    request: Request,
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
            
            # Automatically start P2P seeder server for this file
            try:
                auto_seeder_manager.add_seeder(torrent_filename, uploaded_file_path)
                print(f"🚀 Auto-started P2P seeder for {safe_filename}")
            except Exception as seeder_error:
                print(f"Warning: Failed to auto-start seeder: {seeder_error}")
            
            # Automatically register the uploader as a seeder
            try:
                client_ip = request.client.host
                if client_ip == "127.0.0.1" or client_ip == "localhost":
                    # For local development, try to get real IP from headers
                    client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")
                    if "," in client_ip:
                        client_ip = client_ip.split(",")[0].strip()
                
                # Create announce request for the uploader (as completed seeder)
                # Generate consistent peer ID for uploader as seeder
                uploader_peer_id = BitTorrentUtils.generate_peer_id("P2PS", torrent_data['info_hash'], client_ip)
                
                uploader_announce = TorrentAnnounceRequest(
                    info_hash=torrent_data['info_hash'],
                    peer_id=uploader_peer_id,  # Use consistent peer ID for uploader
                    port=6881,  # Default BitTorrent port
                    uploaded=torrent_data['info']['length'],  # They have uploaded the full file
                    downloaded=torrent_data['info']['length'],  # They have the complete file
                    left=0,  # Nothing left to download
                    event="completed",  # They completed the download (seeding)
                    compact=0
                )
                
                # Register the uploader as a peer/seeder
                tracker_service.announce(uploader_announce, client_ip)
                
            except Exception as peer_reg_error:
                # Don't fail the upload if peer registration fails, just log it
                print(f"Warning: Failed to register uploader as peer: {peer_reg_error}")
            
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

@router.post("/torrents/{info_hash}/seed")
def register_as_seeder(
    info_hash: str,
    request: Request,
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Register the current client as a seeder for an existing torrent"""
    try:
        # Get torrent info
        torrent = tracker_service.get_torrent(info_hash)
        if not torrent:
            raise HTTPException(status_code=404, detail="Torrent not found")
        
        client_ip = request.client.host
        if client_ip == "127.0.0.1" or client_ip == "localhost":
            # For local development, try to get real IP from headers
            client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")
            if "," in client_ip:
                client_ip = client_ip.split(",")[0].strip()
        
        # Create announce request as a completed seeder
        seeder_announce = TorrentAnnounceRequest(
            info_hash=info_hash,
            peer_id=BitTorrentUtils.generate_peer_id(),
            port=6881,
            uploaded=torrent.file_size,  # Full file uploaded
            downloaded=torrent.file_size,  # Full file downloaded
            left=0,  # Nothing left to download
            event="completed",
            compact=0
        )
        
        # Register as peer/seeder
        result = tracker_service.announce(seeder_announce, client_ip)
        
        return {
            "message": f"Successfully registered as seeder for {torrent.name}",
            "info_hash": info_hash,
            "peer_count": len(tracker_service.get_peers(info_hash))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register as seeder: {str(e)}")

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
    stats = tracker_service.get_tracker_stats()
    
    # Add seeder info
    seeder_info = auto_seeder_manager.get_seeder_info()
    stats['active_seeders'] = len(seeder_info)
    stats['seeder_ports'] = [s['port'] for s in seeder_info]
    
    return stats

@router.get("/seeders")
def get_active_seeders():
    """Get information about active P2P seeder servers"""
    return {
        "active_seeders": auto_seeder_manager.get_seeder_info(),
        "count": len(auto_seeder_manager.seeders)
    }

@router.post("/seeders/stop/{info_hash}")
def stop_seeder(info_hash: str):
    """Stop a specific seeder by info hash"""
    if info_hash in auto_seeder_manager.seeders:
        try:
            auto_seeder_manager.seeders[info_hash]['server'].stop_server()
            del auto_seeder_manager.seeders[info_hash]
            return {"message": f"Stopped seeder for {info_hash}"}
        except Exception as e:
            return {"error": f"Failed to stop seeder: {e}"}
    else:
        return {"error": "Seeder not found"}

@router.post("/peers/cleanup")
def cleanup_localhost_peers(
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Remove all localhost (127.0.0.1) peers to avoid duplicate registrations"""
    try:
        count = tracker_service.cleanup_localhost_peers()
        return {"message": f"Removed {count} localhost peers"}
    except Exception as e:
        return {"error": f"Failed to cleanup peers: {e}"}

@router.post("/peers/deduplicate")
def deduplicate_peers(
    tracker_service: TrackerService = Depends(get_tracker_service)
):
    """Remove duplicate peers (same IP:port for same torrent)"""
    try:
        count = tracker_service.deduplicate_peers()
        return {"message": f"Removed {count} duplicate peers"}
    except Exception as e:
        return {"error": f"Failed to deduplicate peers: {e}"}
