#!/usr/bin/env python3
"""
Test script to isolate the torrent creation issue
"""

import sys
import os
import traceback

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.torrent_generator import TorrentGenerator
from app.schemas.torrent import TorrentCreate

def test_torrent_creation():
    """Test torrent creation step by step"""
    try:
        print("Testing torrent creation...")
        
        # Create test file
        test_file = "test_file.txt"
        if not os.path.exists(test_file):
            print(f"Test file {test_file} not found")
            return False
        
        print(f"Using test file: {test_file}")
        
        # Step 1: Generate torrent metadata
        print("Step 1: Generating torrent metadata...")
        tracker_url = "http://localhost:8000/api/tracker/announce"
        torrent_data = TorrentGenerator.create_torrent_metadata(test_file, tracker_url)
        print(f"✓ Torrent metadata created")
        print(f"  Info hash: {torrent_data['info_hash']}")
        print(f"  Name: {torrent_data['info']['name']}")
        print(f"  Size: {torrent_data['info']['length']}")
        
        # Step 2: Convert pieces hash
        print("Step 2: Converting pieces hash...")
        pieces_hash_bytes = bytes.fromhex(torrent_data['info']['pieces'])
        print(f"✓ Pieces hash converted, length: {len(pieces_hash_bytes)} bytes")
        
        # Step 3: Create TorrentCreate object
        print("Step 3: Creating TorrentCreate schema object...")
        torrent_create = TorrentCreate(
            name=torrent_data['info']['name'],
            file_size=torrent_data['info']['length'],
            piece_length=torrent_data['info']['piece length'],
            info_hash=torrent_data['info_hash'],
            num_pieces=len(pieces_hash_bytes) // 20,  # Each SHA-1 hash is 20 bytes
            pieces_hash=pieces_hash_bytes
        )
        print(f"✓ TorrentCreate object created successfully")
        print(f"  Name: {torrent_create.name}")
        print(f"  File size: {torrent_create.file_size}")
        print(f"  Piece length: {torrent_create.piece_length}")
        print(f"  Info hash: {torrent_create.info_hash}")
        print(f"  Num pieces: {torrent_create.num_pieces}")
        print(f"  Pieces hash length: {len(torrent_create.pieces_hash)}")
        
        # Step 4: Test torrent file saving
        print("Step 4: Testing torrent file saving...")
        os.makedirs("torrents", exist_ok=True)
        torrent_filename = os.path.join("torrents", f"{os.path.splitext(test_file)[0]}.torrent")
        saved_path = TorrentGenerator.save_torrent_file(torrent_data, torrent_filename)
        print(f"✓ Torrent file saved: {saved_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_torrent_creation()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Test failed!")
