#!/usr/bin/env python3
"""
Test script to test database operations
"""

import sys
import os
import traceback

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import get_db
from app.services.tracker_service import TrackerService
from app.schemas.torrent import TorrentCreate
from app.utils.torrent_generator import TorrentGenerator

def test_database_operations():
    """Test database operations for torrent creation"""
    try:
        print("Testing database operations...")
        
        # Get database session
        print("Step 1: Getting database session...")
        db_gen = get_db()
        db = next(db_gen)
        print("✓ Database session obtained")
        
        # Create tracker service
        print("Step 2: Creating tracker service...")
        tracker_service = TrackerService(db)
        print("✓ Tracker service created")
        
        # Test file
        test_file = "test_file.txt"
        if not os.path.exists(test_file):
            print(f"Test file {test_file} not found")
            return False
        
        # Generate torrent metadata
        print("Step 3: Generating torrent metadata...")
        tracker_url = "http://localhost:8000/api/tracker/announce"
        torrent_data = TorrentGenerator.create_torrent_metadata(test_file, tracker_url)
        pieces_hash_bytes = bytes.fromhex(torrent_data['info']['pieces'])
        
        # Create TorrentCreate object
        print("Step 4: Creating TorrentCreate object...")
        torrent_create = TorrentCreate(
            name=torrent_data['info']['name'],
            file_size=torrent_data['info']['length'],
            piece_length=torrent_data['info']['piece length'],
            info_hash=torrent_data['info_hash'],
            num_pieces=len(pieces_hash_bytes) // 20,
            pieces_hash=pieces_hash_bytes
        )
        print("✓ TorrentCreate object created")
        
        # Test database insert
        print("Step 5: Testing database insert...")
        result = tracker_service.create_torrent(torrent_create)
        print(f"✓ Torrent created in database with ID: {result.id}")
        print(f"  Name: {result.name}")
        print(f"  Info hash: {result.info_hash}")
        
        # Close database
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during database testing: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_operations()
    if success:
        print("\n🎉 Database tests passed!")
    else:
        print("\n❌ Database test failed!")
