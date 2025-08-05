#!/usr/bin/env python3
"""
P2P Seeder Server - Actually serves file pieces to downloaders
This runs a TCP server that accepts P2P connections and serves file pieces
"""

import os
import sys
import socket
import threading
import time
import hashlib
import struct
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.torrent_generator import TorrentGenerator
from app.utils.bittorrent import BitTorrentUtils
from app.utils.p2p_protocol import P2PProtocol, MessageType

class P2PSeederServer:
    def __init__(self, torrent_file_path: str, original_file_path: str, port: int = 6881):
        self.torrent_file_path = torrent_file_path
        self.original_file_path = original_file_path
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = []
        
        # Load torrent data
        self.torrent_data = TorrentGenerator.load_torrent_file(torrent_file_path)
        self.info_hash = self.torrent_data['info_hash']
        
        # Get local IP for consistent peer ID
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"
        
        # Generate consistent peer ID based on IP and info hash
        self.peer_id = BitTorrentUtils.generate_peer_id("P2PS", self.info_hash, local_ip)
        
        # Load file pieces
        self.file_pieces = self._load_file_pieces()
        
        print(f"🌱 P2P Seeder Server")
        print(f"File: {self.original_file_path}")
        print(f"Port: {self.port}")
        print(f"Info Hash: {self.info_hash}")
        print(f"Peer ID: {self.peer_id}")
        print(f"Pieces: {len(self.file_pieces)}")
    
    def _load_file_pieces(self):
        """Load file and split into pieces"""
        pieces = []
        piece_length = self.torrent_data['info']['piece length']
        
        try:
            with open(self.original_file_path, 'rb') as f:
                piece_index = 0
                while True:
                    piece_data = f.read(piece_length)
                    if not piece_data:
                        break
                    pieces.append(piece_data)
                    piece_index += 1
            
            print(f"📁 Loaded {len(pieces)} pieces from {self.original_file_path}")
            return pieces
            
        except Exception as e:
            print(f"❌ Error loading file pieces: {e}")
            return []
    
    def start_server(self):
        """Start the P2P server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            
            self.running = True
            print(f"🚀 P2P Server started on port {self.port}")
            print(f"📡 Waiting for peer connections...")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"📞 New connection from {client_address}")
                    
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"❌ Error accepting connection: {e}")
                        
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_address):
        """Handle individual client connection"""
        try:
            protocol = P2PProtocol(self.peer_id, self.info_hash)
            
            # Send handshake
            handshake = protocol.create_handshake_message()
            client_socket.send(handshake)
            print(f"🤝 Sent handshake to {client_address}")
            
            # Receive handshake response
            handshake_response = client_socket.recv(1024)
            if len(handshake_response) < 49:
                print(f"❌ Invalid handshake from {client_address}")
                client_socket.close()
                return
            
            # Parse handshake
            try:
                parsed_handshake = protocol.parse_handshake_message(handshake_response)
                print(f"✅ Handshake successful with {client_address}")
                print(f"   Peer ID: {parsed_handshake.get('peer_id', 'Unknown')}")
            except Exception as e:
                print(f"❌ Handshake parse error: {e}")
                client_socket.close()
                return
            
            # Send unchoke message (we're ready to upload)
            unchoke_msg = struct.pack('!IB', 1, MessageType.UNCHOKE)
            client_socket.send(unchoke_msg)
            print(f"🔓 Sent unchoke to {client_address}")
            
            # Send bitfield (we have all pieces)
            bitfield_size = (len(self.file_pieces) + 7) // 8  # Round up to nearest byte
            bitfield = bytearray(bitfield_size)
            for i in range(len(self.file_pieces)):
                byte_index = i // 8
                bit_index = 7 - (i % 8)
                bitfield[byte_index] |= (1 << bit_index)
            
            bitfield_msg = struct.pack(f'!IB{len(bitfield)}s', len(bitfield) + 1, MessageType.BITFIELD, bytes(bitfield))
            client_socket.send(bitfield_msg)
            print(f"📋 Sent bitfield to {client_address} ({len(self.file_pieces)} pieces available)")
            
            # Handle requests
            while True:
                try:
                    # Receive message length
                    length_data = client_socket.recv(4)
                    if len(length_data) != 4:
                        break
                    
                    message_length = struct.unpack('!I', length_data)[0]
                    if message_length == 0:  # Keep-alive
                        continue
                    
                    # Receive message
                    message_data = client_socket.recv(message_length)
                    if len(message_data) != message_length:
                        break
                    
                    message_type = message_data[0]
                    
                    if message_type == MessageType.REQUEST:
                        # Check if we have enough data for REQUEST message (12 bytes for 3 integers)
                        if len(message_data) < 13:  # 1 byte type + 12 bytes data
                            print(f"❌ Invalid REQUEST message length from {client_address}: {len(message_data)} bytes")
                            continue
                            
                        # Parse request: piece_index, offset, length
                        piece_index, offset, length = struct.unpack('!III', message_data[1:13])
                        print(f"📤 Request from {client_address}: piece {piece_index}, offset {offset}, length {length}")
                        
                        # Send piece
                        if piece_index < len(self.file_pieces):
                            piece_data = self.file_pieces[piece_index]
                            if offset < len(piece_data):
                                chunk = piece_data[offset:offset + length]
                                piece_msg = struct.pack(f'!IBII{len(chunk)}s', 
                                                      9 + len(chunk), 
                                                      MessageType.PIECE, 
                                                      piece_index, 
                                                      offset, 
                                                      chunk)
                                client_socket.send(piece_msg)
                                print(f"✅ Sent piece {piece_index} chunk ({len(chunk)} bytes) to {client_address}")
                            else:
                                print(f"❌ Invalid offset {offset} for piece {piece_index}")
                        else:
                            print(f"❌ Invalid piece index {piece_index}")
                    
                    elif message_type == MessageType.INTERESTED:
                        print(f"😊 {client_address} is interested")
                        # Send unchoke again
                        unchoke_msg = struct.pack('!IB', 1, MessageType.UNCHOKE)
                        client_socket.send(unchoke_msg)
                    
                    elif message_type == MessageType.NOT_INTERESTED:
                        print(f"😐 {client_address} is not interested")
                    
                    else:
                        print(f"🔍 Unknown message type {message_type} from {client_address}")
                
                except Exception as e:
                    print(f"❌ Error handling message from {client_address}: {e}")
                    break
            
        except Exception as e:
            print(f"❌ Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"👋 Disconnected from {client_address}")
    
    def stop_server(self):
        """Stop the P2P server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("🛑 P2P Server stopped")

def main():
    if len(sys.argv) != 3:
        print("Usage: python p2p_seeder_server.py <torrent_file> <original_file>")
        print("Example: python p2p_seeder_server.py file.torrent file.txt")
        return
    
    torrent_file = sys.argv[1]
    original_file = sys.argv[2]
    
    if not os.path.exists(torrent_file):
        print(f"❌ Torrent file not found: {torrent_file}")
        return
    
    if not os.path.exists(original_file):
        print(f"❌ Original file not found: {original_file}")
        return
    
    server = P2PSeederServer(torrent_file, original_file)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.stop_server()

if __name__ == "__main__":
    main()
