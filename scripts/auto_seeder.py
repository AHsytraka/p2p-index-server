#!/usr/bin/env python3
"""
Auto Seeder - Register as a seeder for all uploaded torrents
This will automatically register your machine as a seeder for torrents you have uploaded
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.torrent_generator import TorrentGenerator
from app.utils.bittorrent import BitTorrentUtils

def main():
    print("🌱 Auto Seeder - Registering as seeder for uploaded torrents")
    
    tracker_url = "http://localhost:8000"
    peer_id = BitTorrentUtils.generate_peer_id()
    peer_port = 6881
    
    print(f"Peer ID: {peer_id}")
    print(f"Port: {peer_port}")
    print(f"Tracker: {tracker_url}")
    
    # Directories
    torrents_dir = "torrents"
    uploads_dir = "uploads"
    
    if not os.path.exists(torrents_dir):
        print(f"❌ Torrents directory '{torrents_dir}' not found")
        return
    
    if not os.path.exists(uploads_dir):
        print(f"❌ Uploads directory '{uploads_dir}' not found")
        return
    
    # Find all torrent files
    torrent_files = []
    for file in os.listdir(torrents_dir):
        if file.endswith('.torrent'):
            torrent_files.append(os.path.join(torrents_dir, file))
    
    print(f"📁 Found {len(torrent_files)} torrent files")
    
    if not torrent_files:
        print("No torrent files found to seed")
        return
    
    successful = 0
    
    for torrent_path in torrent_files:
        try:
            print(f"\n📡 Processing: {os.path.basename(torrent_path)}")
            
            # Load torrent data
            torrent_data = TorrentGenerator.load_torrent_file(torrent_path)
            info_hash = torrent_data['info_hash']
            file_name = torrent_data['info']['name']
            
            print(f"  File: {file_name}")
            print(f"  Info Hash: {info_hash}")
            
            # Check if we have the actual file
            file_path = os.path.join(uploads_dir, file_name)
            if not os.path.exists(file_path):
                print(f"  ⚠️  File not found in uploads directory, skipping...")
                continue
            
            file_size = os.path.getsize(file_path)
            print(f"  Size: {BitTorrentUtils.format_bytes(file_size)}")
            
            # Register as seeder by announcing completion
            announce_params = {
                'info_hash': info_hash,
                'peer_id': peer_id,
                'port': peer_port,
                'uploaded': file_size,
                'downloaded': file_size,
                'left': 0,  # Nothing left to download (we have complete file)
                'event': 'completed',
                'compact': 0
            }
            
            print(f"  📡 Announcing to tracker...")
            
            response = requests.get(
                f"{tracker_url}/api/tracker/announce",
                params=announce_params,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  ✅ Successfully registered as seeder!")
                successful += 1
                
                # Also send a regular announce to stay active
                announce_params['event'] = ''  # Remove completed event
                response2 = requests.get(
                    f"{tracker_url}/api/tracker/announce",
                    params=announce_params,
                    timeout=10
                )
                
                if response2.status_code == 200:
                    print(f"  💓 Active seeder status confirmed")
                
            else:
                print(f"  ❌ Failed to register: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        time.sleep(1)  # Small delay between registrations
    
    print(f"\n📊 Summary:")
    print(f"Total torrents processed: {len(torrent_files)}")
    print(f"Successfully registered as seeder: {successful}")
    print(f"Failed: {len(torrent_files) - successful}")
    
    if successful > 0:
        print(f"\n🎉 You are now registered as a seeder for {successful} torrents!")
        print("Other peers can now discover and download from you.")
        print("Try downloading from the desktop client again - you should now see yourself as a peer!")

if __name__ == "__main__":
    main()
