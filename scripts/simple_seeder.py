#!/usr/bin/env python3
"""
Simple Seeder for Testing P2P Downloads
This creates a peer that can serve file pieces to downloaders
"""

import sys
import os
import threading
import time
import socket
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.torrent_generator import TorrentGenerator
from app.utils.bittorrent import BitTorrentUtils
import requests

class SimpleSeeder:
    """A simple seeder that can serve file pieces"""
    
    def __init__(self, torrent_file_path: str, original_file_path: str, port: int = 6881):
        self.torrent_file_path = torrent_file_path
        self.original_file_path = original_file_path
        self.port = port
        self.peer_id = BitTorrentUtils.generate_peer_id("SEED")
        self.tracker_url = "http://localhost:8000"
        
        # Load torrent data
        self.torrent_data = TorrentGenerator.load_torrent_file(torrent_file_path)
        self.info_hash = self.torrent_data['info_hash']
        
        print(f"🌱 Simple Seeder Started")
        print(f"📁 File: {original_file_path}")
        print(f"🔗 Torrent: {torrent_file_path}")
        print(f"🆔 Peer ID: {self.peer_id}")
        print(f"📡 Port: {port}")
        print(f"🎯 Info Hash: {self.info_hash}")
        
    def start_seeding(self):
        """Start seeding the file"""
        # Announce to tracker as a seeder
        self.announce_to_tracker()
        
        # Start listening for connections (simplified)
        self.start_listening()
        
        # Keep announcing periodically
        self.start_announce_loop()
        
    def announce_to_tracker(self):
        """Announce to tracker that we're seeding"""
        try:
            announce_params = {
                'info_hash': self.info_hash,
                'peer_id': self.peer_id,
                'port': self.port,
                'uploaded': 0,
                'downloaded': 0,
                'left': 0,  # 0 means we have the complete file (seeder)
                'event': 'started'
            }
            
            response = requests.get(f"{self.tracker_url}/api/tracker/announce", 
                                  params=announce_params, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Successfully announced to tracker")
                data = response.json()
                print(f"📊 Tracker response: {len(data.get('peers', []))} peers")
            else:
                print(f"❌ Failed to announce to tracker: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error announcing to tracker: {e}")
    
    def start_listening(self):
        """Start listening for peer connections (simplified)"""
        def listen_thread():
            try:
                # Create a simple socket server
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('localhost', self.port))
                server_socket.listen(5)
                
                print(f"🎧 Listening for connections on port {self.port}")
                
                while True:
                    try:
                        client_socket, addr = server_socket.accept()
                        print(f"🔌 Incoming connection from {addr}")
                        
                        # Handle connection in a separate thread
                        threading.Thread(
                            target=self.handle_peer_connection, 
                            args=(client_socket, addr),
                            daemon=True
                        ).start()
                        
                    except Exception as e:
                        print(f"⚠️ Error accepting connection: {e}")
                        
            except Exception as e:
                print(f"❌ Error starting listener: {e}")
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def handle_peer_connection(self, client_socket, addr):
        """Handle a peer connection (simplified)"""
        try:
            print(f"📡 Handling peer {addr}")
            
            # In a real implementation, this would handle BitTorrent protocol messages
            # For now, just acknowledge the connection
            
            # Read any incoming data
            data = client_socket.recv(1024)
            if data:
                print(f"📨 Received {len(data)} bytes from {addr}")
            
            # Send a simple response
            response = f"SEEDER:{self.peer_id}:{self.info_hash}".encode()
            client_socket.send(response)
            
            # Keep connection alive for a bit
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ Error handling peer {addr}: {e}")
        finally:
            client_socket.close()
            print(f"🔌 Connection closed with {addr}")
    
    def start_announce_loop(self):
        """Periodically announce to tracker"""
        def announce_loop():
            while True:
                time.sleep(30)  # Announce every 30 seconds
                self.announce_to_tracker()
        
        threading.Thread(target=announce_loop, daemon=True).start()

def main():
    """Main function to start seeder"""
    if len(sys.argv) != 3:
        print("Usage: python simple_seeder.py <torrent_file> <original_file>")
        print("Example: python simple_seeder.py test_file.torrent test_file.txt")
        sys.exit(1)
    
    torrent_file = sys.argv[1]
    original_file = sys.argv[2]
    
    if not os.path.exists(torrent_file):
        print(f"❌ Torrent file not found: {torrent_file}")
        sys.exit(1)
    
    if not os.path.exists(original_file):
        print(f"❌ Original file not found: {original_file}")
        sys.exit(1)
    
    # Create seeder
    seeder = SimpleSeeder(torrent_file, original_file)
    
    try:
        # Start seeding
        seeder.start_seeding()
        
        print("🌱 Seeder is running! Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping seeder...")
    except Exception as e:
        print(f"❌ Seeder error: {e}")

if __name__ == "__main__":
    main()
