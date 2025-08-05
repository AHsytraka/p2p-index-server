#!/usr/bin/env python3
"""
Auto P2P Seeder - Automatically start P2P servers for all your torrents
This will start actual P2P servers that can serve file pieces to downloaders
"""

import os
import sys
import threading
import time
import signal
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.p2p_seeder_server import P2PSeederServer
from app.utils.torrent_generator import TorrentGenerator

class AutoP2PSeeder:
    def __init__(self):
        self.servers = []
        self.running = True
        self.base_port = 6881
        
    def find_torrent_file_pairs(self):
        """Find torrent files and their corresponding data files"""
        pairs = []
        torrents_dir = "torrents"
        uploads_dir = "uploads"
        
        if not os.path.exists(torrents_dir):
            print(f"❌ Torrents directory '{torrents_dir}' not found")
            return pairs
        
        if not os.path.exists(uploads_dir):
            print(f"❌ Uploads directory '{uploads_dir}' not found")
            return pairs
        
        for torrent_file in os.listdir(torrents_dir):
            if torrent_file.endswith('.torrent'):
                torrent_path = os.path.join(torrents_dir, torrent_file)
                
                try:
                    # Load torrent to get the original file name
                    torrent_data = TorrentGenerator.load_torrent_file(torrent_path)
                    original_filename = torrent_data['info']['name']
                    original_file_path = os.path.join(uploads_dir, original_filename)
                    
                    if os.path.exists(original_file_path):
                        pairs.append((torrent_path, original_file_path))
                        print(f"✅ Found pair: {torrent_file} -> {original_filename}")
                    else:
                        print(f"⚠️  Torrent without file: {torrent_file} (missing {original_filename})")
                        
                except Exception as e:
                    print(f"❌ Error processing {torrent_file}: {e}")
        
        return pairs
    
    def start_seeders(self):
        """Start P2P seeder servers for all torrent-file pairs"""
        pairs = self.find_torrent_file_pairs()
        
        if not pairs:
            print("No torrent-file pairs found to seed")
            return
        
        print(f"\n🚀 Starting P2P seeder servers...")
        
        for i, (torrent_path, file_path) in enumerate(pairs):
            port = self.base_port + i
            
            try:
                server = P2PSeederServer(torrent_path, file_path, port)
                
                # Start server in a separate thread
                server_thread = threading.Thread(
                    target=server.start_server,
                    daemon=True
                )
                server_thread.start()
                
                self.servers.append(server)
                print(f"✅ Started seeder for {os.path.basename(file_path)} on port {port}")
                
                # Small delay between server starts
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Failed to start seeder for {os.path.basename(file_path)}: {e}")
        
        print(f"\n📡 {len(self.servers)} P2P seeder servers are running")
        print("Peers can now connect and download file pieces!")
        print("Press Ctrl+C to stop all servers")
    
    def stop_all_servers(self):
        """Stop all running seeder servers"""
        print(f"\n🛑 Stopping {len(self.servers)} seeder servers...")
        for server in self.servers:
            try:
                server.stop_server()
            except:
                pass
        self.servers.clear()
        print("All servers stopped")
    
    def run(self):
        """Run the auto seeder"""
        print("🌱 Auto P2P Seeder - Starting actual P2P servers")
        print("This will start TCP servers that can serve file pieces to downloaders")
        
        try:
            self.start_seeders()
            
            if self.servers:
                # Keep the main thread alive
                while self.running:
                    time.sleep(1)
            else:
                print("No servers started")
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.stop_all_servers()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Received interrupt signal")
    sys.exit(0)

def main():
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    auto_seeder = AutoP2PSeeder()
    auto_seeder.run()

if __name__ == "__main__":
    main()
