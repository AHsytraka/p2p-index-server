#!/usr/bin/env python3
"""
Simple P2P BitTorrent-like Client
This is a basic implementation for the MVP
"""

import argparse
import asyncio
import os
import sys
import json
import requests
from typing import Dict, Any, List, Optional

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.torrent_generator import TorrentGenerator
from app.utils.download_manager import DownloadManager
from app.utils.bittorrent import BitTorrentUtils
from app.utils.file_manager import FileManager

class P2PClient:
    """Simple P2P BitTorrent-like client"""
    
    def __init__(self, tracker_url: str = "http://localhost:8000/api/tracker"):
        self.tracker_url = tracker_url
        self.peer_id = BitTorrentUtils.generate_peer_id()
        self.port = 6881  # Default BitTorrent port
        self.downloads: Dict[str, DownloadManager] = {}
        
    def create_torrent(self, file_path: str, output_dir: str = ".") -> str:
        """Create a torrent file for sharing"""
        try:
            print(f"Creating torrent for: {file_path}")
            
            # Generate torrent metadata
            torrent_data = TorrentGenerator.create_torrent_metadata(
                file_path, 
                f"{self.tracker_url}/announce"
            )
            
            # Save torrent file locally with proper naming
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
            torrent_filename = os.path.join(output_dir, f"{base_name}.torrent")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            TorrentGenerator.save_torrent_file(torrent_data, torrent_filename)
            
            print(f"Torrent file created: {torrent_filename}")
            print(f"Info hash: {torrent_data['info_hash']}")
            
            # Register torrent with tracker
            self._register_torrent_with_tracker(torrent_data)
            
            return torrent_filename
            
        except Exception as e:
            print(f"Error creating torrent: {e}")
            return ""
    
    def _register_torrent_with_tracker(self, torrent_data: Dict[str, Any]):
        """Register torrent with the tracker via file upload"""
        try:
            # For this MVP, we'll use the upload endpoint
            # In a real implementation, you might register metadata directly
            print("Registering torrent with tracker...")
            
            # Create a temporary torrent file for upload
            temp_torrent = "temp_upload.torrent"
            TorrentGenerator.save_torrent_file(torrent_data, temp_torrent)
            
            # Read the original file for upload
            original_file = torrent_data['info']['name']
            if os.path.exists(original_file):
                with open(original_file, 'rb') as f:
                    files = {'file': (original_file, f, 'application/octet-stream')}
                    response = requests.post(f"{self.tracker_url}/upload", files=files)
                
                if response.status_code == 200:
                    print("✓ Torrent registered successfully with tracker")
                else:
                    print(f"✗ Failed to register torrent: {response.text}")
            
            # Clean up temp file
            if os.path.exists(temp_torrent):
                os.remove(temp_torrent)
                
        except Exception as e:
            print(f"Error registering with tracker: {e}")
    
    def download_torrent(self, torrent_file: str, download_dir: str = "./downloads"):
        """Start downloading a torrent"""
        try:
            print(f"Loading torrent: {torrent_file}")
            
            # Load torrent metadata
            torrent_data = TorrentGenerator.load_torrent_file(torrent_file)
            info_hash = torrent_data['info_hash']
            file_name = torrent_data['info']['name']
            
            # Create download directory
            os.makedirs(download_dir, exist_ok=True)
            output_path = os.path.join(download_dir, file_name)
            
            print(f"Starting download of: {file_name}")
            print(f"Info hash: {info_hash}")
            print(f"Output path: {output_path}")
            
            # Get peers from tracker
            peers = self._get_peers_from_tracker(info_hash)
            if not peers:
                print("No peers found for this torrent")
                return
            
            print(f"Found {len(peers)} peers")
            
            # Start download manager
            download_manager = DownloadManager(torrent_data, output_path)
            self.downloads[info_hash] = download_manager
            
            # Add peers
            for peer in peers[:5]:  # Limit to 5 peers for MVP
                print(f"Connecting to peer: {peer['ip_address']}:{peer['port']}")
                download_manager.add_peer(peer['peer_id'], peer['ip_address'], peer['port'])
            
            # Start download
            download_manager.start_download()
            
            # Monitor progress
            self._monitor_download(info_hash, download_manager)
            
        except Exception as e:
            print(f"Error downloading torrent: {e}")
    
    def _get_peers_from_tracker(self, info_hash: str) -> List[Dict]:
        """Get peer list from tracker"""
        try:
            # Announce to tracker
            announce_url = f"{self.tracker_url}/announce"
            params = {
                'info_hash': info_hash,
                'peer_id': self.peer_id,
                'port': self.port,
                'uploaded': 0,
                'downloaded': 0,
                'left': 1000000,  # Placeholder
                'event': 'started'
            }
            
            response = requests.get(announce_url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('peers', [])
            else:
                print(f"Tracker announce failed: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error contacting tracker: {e}")
            return []
    
    def _monitor_download(self, info_hash: str, download_manager: DownloadManager):
        """Monitor download progress"""
        print("\nDownload Progress:")
        print("-" * 50)
        
        try:
            while not download_manager.piece_manager.is_complete():
                progress = download_manager.get_progress()
                
                print(f"\rProgress: {progress['completion_percentage']:.1f}% "
                      f"({progress['downloaded_pieces']}/{progress['total_pieces']} pieces) "
                      f"Peers: {progress['connected_peers']} "
                      f"Speed: {BitTorrentUtils.format_speed(progress['download_speed'])}", 
                      end="", flush=True)
                
                import time
                time.sleep(1)
            
            print(f"\n✓ Download completed!")
            
        except KeyboardInterrupt:
            print(f"\n✗ Download interrupted by user")
            download_manager.stop_download()
        except Exception as e:
            print(f"\n✗ Download error: {e}")
            download_manager.stop_download()
    
    def list_downloads(self):
        """List active downloads"""
        if not self.downloads:
            print("No active downloads")
            return
        
        print("Active Downloads:")
        print("-" * 50)
        for info_hash, manager in self.downloads.items():
            progress = manager.get_progress()
            print(f"Hash: {info_hash[:16]}...")
            print(f"Progress: {progress['completion_percentage']:.1f}%")
            print(f"Pieces: {progress['downloaded_pieces']}/{progress['total_pieces']}")
            print(f"Peers: {progress['connected_peers']}")
            print("-" * 30)

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="P2P BitTorrent-like Client")
    parser.add_argument("--tracker", default="http://localhost:8000/api/tracker", 
                       help="Tracker URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create torrent command
    create_parser = subparsers.add_parser("create", help="Create a torrent file")
    create_parser.add_argument("file", help="File to create torrent for")
    create_parser.add_argument("-o", "--output", default=".", help="Output directory")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download a torrent")
    download_parser.add_argument("torrent", help="Torrent file to download")
    download_parser.add_argument("-d", "--dir", default="./downloads", help="Download directory")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List active downloads")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = P2PClient(args.tracker)
    
    if args.command == "create":
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            return
        
        torrent_file = client.create_torrent(args.file, args.output)
        if torrent_file:
            print(f"\nTorrent created successfully!")
            print(f"Share this file: {torrent_file}")
    
    elif args.command == "download":
        if not os.path.exists(args.torrent):
            print(f"Error: Torrent file not found: {args.torrent}")
            return
        
        client.download_torrent(args.torrent, args.dir)
    
    elif args.command == "list":
        client.list_downloads()

if __name__ == "__main__":
    main()
