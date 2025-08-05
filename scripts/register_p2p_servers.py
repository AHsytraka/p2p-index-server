#!/usr/bin/env python3
"""
Register P2P Servers - Register running P2P servers as peers in the tracker
"""

import os
import sys
import requests
import threading
import time

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.torrent_generator import TorrentGenerator
from app.utils.bittorrent import BitTorrentUtils

def register_seeder_with_tracker(torrent_path: str, port: int, tracker_url: str = "http://localhost:8000"):
    """Register a running P2P seeder with the tracker"""
    try:
        # Load torrent data
        torrent_data = TorrentGenerator.load_torrent_file(torrent_path)
        info_hash = torrent_data['info_hash']
        file_name = torrent_data['info']['name']
        file_size = torrent_data['info']['length']
        
        print(f"📡 Registering {file_name} on port {port}")
        
        # Generate peer ID
        peer_id = BitTorrentUtils.generate_peer_id()
        
        # Register as completed seeder
        announce_params = {
            'info_hash': info_hash,
            'peer_id': peer_id,
            'port': port,  # Use the actual P2P server port
            'uploaded': file_size,
            'downloaded': file_size,
            'left': 0,
            'event': 'completed',
            'compact': 0
        }
        
        response = requests.get(
            f"{tracker_url}/api/tracker/announce",
            params=announce_params,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Registered {file_name} as seeder on port {port}")
            return True
        else:
            print(f"❌ Failed to register {file_name}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error registering {torrent_path}: {e}")
        return False

def main():
    """Register all P2P servers that should be running"""
    print("📡 Registering P2P seeder servers with tracker...")
    
    # Define the torrents and their expected ports (based on auto_p2p_seeder.py)
    torrents_dir = "torrents"
    base_port = 6881
    
    if not os.path.exists(torrents_dir):
        print(f"❌ Torrents directory not found: {torrents_dir}")
        return
    
    torrent_files = [f for f in os.listdir(torrents_dir) if f.endswith('.torrent')]
    
    successful = 0
    for i, torrent_file in enumerate(torrent_files):
        torrent_path = os.path.join(torrents_dir, torrent_file)
        port = base_port + i
        
        if register_seeder_with_tracker(torrent_path, port):
            successful += 1
        
        time.sleep(0.5)  # Small delay between registrations
    
    print(f"\n📊 Summary:")
    print(f"Total torrents: {len(torrent_files)}")
    print(f"Successfully registered: {successful}")
    print(f"Failed: {len(torrent_files) - successful}")
    
    if successful > 0:
        print(f"\n🎉 {successful} P2P servers are now registered in the tracker!")
        print("Desktop client should now be able to connect to these peers.")

if __name__ == "__main__":
    main()
