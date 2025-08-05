"""
Automatic P2P Seeder Manager
Automatically starts P2P seeder servers for uploaded files
"""

import os
import threading
import time
from typing import Dict, List
import asyncio
from pathlib import Path

from app.utils.torrent_generator import TorrentGenerator
from app.utils.bittorrent import BitTorrentUtils
from scripts.p2p_seeder_server import P2PSeederServer

class AutoSeederManager:
    """Manages automatic P2P seeder servers"""
    
    def __init__(self):
        self.seeders: Dict[str, P2PSeederServer] = {}
        self.base_port = 6881
        self.next_port = self.base_port
        self.running = False
        
    def start_manager(self):
        """Start the auto seeder manager"""
        self.running = True
        
        # Start existing torrents in a background thread
        startup_thread = threading.Thread(target=self._start_existing_seeders, daemon=True)
        startup_thread.start()
        
        print("🌱 Auto Seeder Manager started")
    
    def _start_existing_seeders(self):
        """Start seeder servers for existing torrent files"""
        try:
            torrents_dir = "torrents"
            uploads_dir = "uploads"
            
            if not os.path.exists(torrents_dir) or not os.path.exists(uploads_dir):
                return
            
            torrent_files = [f for f in os.listdir(torrents_dir) if f.endswith('.torrent')]
            
            for torrent_file in torrent_files:
                torrent_path = os.path.join(torrents_dir, torrent_file)
                
                try:
                    torrent_data = TorrentGenerator.load_torrent_file(torrent_path)
                    original_filename = torrent_data['info']['name']
                    original_file_path = os.path.join(uploads_dir, original_filename)
                    
                    if os.path.exists(original_file_path):
                        self.add_seeder(torrent_path, original_file_path)
                        time.sleep(0.2)  # Small delay between server starts
                        
                except Exception as e:
                    print(f"Warning: Failed to start seeder for {torrent_file}: {e}")
            
            if self.seeders:
                print(f"✅ Started {len(self.seeders)} P2P seeder servers automatically")
                
        except Exception as e:
            print(f"Warning: Error starting existing seeders: {e}")
    
    def add_seeder(self, torrent_path: str, file_path: str) -> bool:
        """Add a new seeder server"""
        try:
            # Load torrent to get info hash
            torrent_data = TorrentGenerator.load_torrent_file(torrent_path)
            info_hash = torrent_data['info_hash']
            
            # Check if already seeding
            if info_hash in self.seeders:
                print(f"Already seeding {os.path.basename(file_path)}")
                return True
            
            # Find available port
            port = self._get_next_port()
            
            # Create and start seeder
            seeder = P2PSeederServer(torrent_path, file_path, port)
            
            # Start seeder in background thread
            seeder_thread = threading.Thread(target=seeder.start_server, daemon=True)
            seeder_thread.start()
            
            # Store seeder info
            self.seeders[info_hash] = {
                'server': seeder,
                'port': port,
                'file_path': file_path,
                'thread': seeder_thread
            }
            
            print(f"🚀 Started P2P seeder for {os.path.basename(file_path)} on port {port}")
            
            # Register with tracker in background
            self._register_with_tracker_async(info_hash, port, torrent_data)
            
            return True
            
        except Exception as e:
            print(f"Error adding seeder for {file_path}: {e}")
            return False
    
    def _get_next_port(self) -> int:
        """Get the next available port"""
        port = self.next_port
        self.next_port += 1
        return port
    
    def _register_with_tracker_async(self, info_hash: str, port: int, torrent_data: dict):
        """Register seeder with tracker in background"""
        def register():
            try:
                import requests
                import socket
                
                time.sleep(1)  # Wait for server to fully start
                
                # Get the actual network IP instead of using localhost
                def get_local_ip():
                    """Get the local network IP address"""
                    try:
                        # Connect to a remote address to determine local IP
                        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                            s.connect(("8.8.8.8", 80))
                            return s.getsockname()[0]
                    except:
                        return "127.0.0.1"
                
                local_ip = get_local_ip()
                
                # Use a consistent peer ID based on info_hash and port to avoid duplicates
                import hashlib
                peer_id_seed = f"SEEDER_{info_hash}_{port}_{local_ip}"
                peer_id_hash = hashlib.md5(peer_id_seed.encode()).hexdigest()[:16]
                peer_id = f"P2PS{peer_id_hash}"  # Consistent seeder peer ID (20 chars)
                
                file_size = torrent_data['info']['length']
                
                announce_params = {
                    'info_hash': info_hash,
                    'peer_id': peer_id,
                    'port': port,
                    'uploaded': file_size,
                    'downloaded': file_size,
                    'left': 0,
                    'event': 'completed',
                    'compact': 0,
                    'ip': local_ip  # Explicitly specify the IP address
                }
                
                # Use localhost to connect to tracker but specify network IP
                response = requests.get(
                    "http://localhost:8000/api/tracker/announce",
                    params=announce_params,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"✅ Registered seeder for port {port} with tracker (IP: {local_ip})")
                else:
                    print(f"⚠️  Failed to register seeder with tracker: {response.text}")
                    
            except Exception as e:
                print(f"⚠️  Failed to register seeder with tracker: {e}")
        
        threading.Thread(target=register, daemon=True).start()
    
    def stop_manager(self):
        """Stop the auto seeder manager and all seeders"""
        self.running = False
        for info_hash, seeder_info in self.seeders.items():
            try:
                seeder_info['server'].stop_server()
            except:
                pass
        self.seeders.clear()
        print("🛑 Auto Seeder Manager stopped")
    
    def get_seeder_info(self) -> List[dict]:
        """Get information about running seeders"""
        info = []
        for info_hash, seeder_info in self.seeders.items():
            info.append({
                'info_hash': info_hash,
                'port': seeder_info['port'],
                'file_path': seeder_info['file_path'],
                'status': 'running'
            })
        return info

# Global instance
auto_seeder_manager = AutoSeederManager()
