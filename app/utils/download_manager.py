import threading
import time
import struct
from typing import Dict, List, Optional
from app.utils.p2p_protocol import P2PProtocol, MessageType
from app.utils.piece_manager import PieceManager
from app.utils.file_manager import FileManager

class DownloadManager:
    """Manages file downloads from multiple peers"""
    
    def __init__(self, torrent_info: Dict, output_path: str):
        self.torrent_info = torrent_info
        self.output_path = output_path
        self.info_hash = torrent_info['info_hash']
        
        # Calculate total pieces correctly - pieces is a hex string, each hash is 40 hex chars (20 bytes)
        pieces_hex = torrent_info['info']['pieces']
        self.total_pieces = len(pieces_hex) // 40  # Each SHA-1 hash is 40 hex characters
        
        self.piece_manager = PieceManager(self.total_pieces)
        self.peer_connections: Dict[str, P2PProtocol] = {}
        self.downloaded_pieces: Dict[int, bytearray] = {}
        self.piece_chunks: Dict[int, Dict[int, bool]] = {}  # Track chunks for each piece
        
        self.download_speed = 0.0
        self.upload_speed = 0.0
        self.is_downloading = False
        self.is_paused = False
        self.download_thread: Optional[threading.Thread] = None
        
        self.lock = threading.Lock()
        
    def add_peer(self, peer_id: str, ip: str, port: int) -> bool:
        """Add a peer to download from"""
        try:
            peer_key = f"{ip}:{port}"
            
            # Check if we already have a connection to this peer
            if peer_key in self.peer_connections:
                print(f"Already connected to peer {peer_key}")
                return True
            
            protocol = P2PProtocol(peer_id, self.info_hash)
            
            if protocol.connect_to_peer(ip, port):
                with self.lock:
                    self.peer_connections[peer_key] = protocol
                
                # Send interested message
                protocol.send_message(MessageType.INTERESTED)
                print(f"✅ Connected to peer {peer_key}")
                return True
            return False
            
        except Exception as e:
            print(f"Failed to add peer {ip}:{port}: {e}")
            return False
    
    def start_download(self) -> None:
        """Start the download process"""
        if self.is_downloading:
            return
        
        self.is_downloading = True
        self.download_thread = threading.Thread(target=self._download_loop)
        self.download_thread.start()
    
    def stop_download(self) -> None:
        """Stop the download process"""
        self.is_downloading = False
        
        if self.download_thread:
            self.download_thread.join()
        
        # Disconnect from all peers
        with self.lock:
            for protocol in self.peer_connections.values():
                protocol.disconnect()
            self.peer_connections.clear()
    
    def _download_loop(self) -> None:
        """Main download loop"""
        while self.is_downloading and not self.piece_manager.is_complete():
            # Check if paused
            if self.is_paused:
                time.sleep(0.5)  # Sleep longer when paused
                continue
                
            # Request pieces from available peers
            self._request_pieces()
            
            # Handle incoming messages
            self._handle_peer_messages()
            
            # Update download statistics
            self._update_statistics()
            
            time.sleep(0.1)  # Small delay to prevent busy waiting
        
        if self.piece_manager.is_complete():
            self._reconstruct_file()
    
    def _request_pieces(self) -> None:
        """Request pieces from peers"""
        with self.lock:
            for peer_addr, protocol in self.peer_connections.items():
                piece_index = self.piece_manager.get_next_piece_to_request()
                
                if piece_index >= 0:
                    self.piece_manager.mark_piece_requested(piece_index)
                    
                    # Request the entire piece (simplified approach)
                    piece_length = self.torrent_info['info']['piece length']
                    
                    # For the last piece, it might be smaller
                    if piece_index == self.total_pieces - 1:
                        file_size = self.torrent_info['info']['length']
                        last_piece_size = file_size % piece_length
                        if last_piece_size > 0:
                            piece_length = last_piece_size
                    
                    begin = 0  # Start from beginning of piece
                    length = piece_length  # Request entire piece at once
                    
                    request_payload = struct.pack('!III', piece_index, begin, length)
                    if protocol.send_message(MessageType.REQUEST, request_payload):
                        print(f"📤 Requested entire piece {piece_index} (offset {begin}, length {length}) from {peer_addr}")
                    else:
                        print(f"❌ Failed to send request to {peer_addr}")
                        # Mark piece as not requested if send failed
                        self.piece_manager.mark_piece_not_requested(piece_index)
    
    def _handle_peer_messages(self) -> None:
        """Handle messages from peers"""
        with self.lock:
            for peer_addr, protocol in list(self.peer_connections.items()):
                try:
                    message = protocol.receive_message()
                    
                    if message is None:
                        continue  # Timeout or no message, keep connection
                    
                    message_type = message.get('type')
                    
                    if message_type == MessageType.PIECE:
                        self._handle_piece_message(message['payload'])
                    elif message_type == MessageType.HAVE:
                        piece_index = struct.unpack('!I', message['payload'])[0]
                        self.piece_manager.update_peer_pieces(peer_addr, [piece_index])
                    elif message_type == MessageType.BITFIELD:
                        self._handle_bitfield_message(peer_addr, message['payload'])
                    elif message_type == MessageType.UNCHOKE:
                        print(f"Peer {peer_addr} unchoked us")
                    elif message_type == 'keep_alive':
                        # Send keep alive back
                        protocol.send_message(MessageType.KEEP_ALIVE)
                        
                except Exception as e:
                    print(f"Error handling message from {peer_addr}: {e}")
                    # Don't disconnect on every error, just skip this iteration
                    continue
                    
    def _handle_bitfield_message(self, peer_addr: str, payload: bytes) -> None:
        """Handle bitfield message showing which pieces peer has"""
        available_pieces = []
        for byte_index, byte_val in enumerate(payload):
            for bit_index in range(8):
                piece_index = byte_index * 8 + bit_index
                if piece_index >= self.total_pieces:
                    break
                if byte_val & (1 << (7 - bit_index)):
                    available_pieces.append(piece_index)
        
        self.piece_manager.update_peer_pieces(peer_addr, available_pieces)
        print(f"Peer {peer_addr} has {len(available_pieces)} pieces available")
    
    def _handle_piece_message(self, payload: bytes) -> None:
        """Handle received piece data"""
        if len(payload) < 8:  # Need at least piece_index (4) + offset (4)
            return
        
        # Parse PIECE message: piece_index, offset, chunk_data
        piece_index = struct.unpack('!I', payload[0:4])[0]
        offset = struct.unpack('!I', payload[4:8])[0]
        chunk_data = payload[8:]
        
        print(f"📥 Received piece {piece_index}, offset {offset}, length {len(chunk_data)}")
        
        # Since we're requesting entire pieces, offset should be 0
        if offset == 0:
            # Store the entire piece
            self.downloaded_pieces[piece_index] = bytearray(chunk_data)
            self.piece_manager.mark_piece_completed(piece_index)
            print(f"✅ Piece {piece_index} completed ({len(chunk_data)} bytes)")
        else:
            print(f"❌ Unexpected offset {offset} for piece {piece_index} (expected 0)")
    
    def _update_statistics(self) -> None:
        """Update download statistics"""
        # This would calculate actual speeds based on data transfer
        # For now, just placeholder values
        self.download_speed = len(self.downloaded_pieces) * 1024  # Simplified
    
    def _reconstruct_file(self) -> None:
        """Reconstruct the complete file from pieces"""
        ordered_pieces = []
        
        for i in range(self.total_pieces):
            if i in self.downloaded_pieces:
                piece_data = self.downloaded_pieces[i]
                # Convert bytearray to bytes if needed
                if isinstance(piece_data, bytearray):
                    piece_data = bytes(piece_data)
                ordered_pieces.append(piece_data)
            else:
                print(f"Missing piece {i}")
                return
        
        FileManager.reconstruct_file(ordered_pieces, self.output_path)
        print(f"File download completed: {self.output_path}")
    
    def get_progress(self) -> Dict:
        """Get download progress information"""
        return {
            'completion_percentage': self.piece_manager.get_completion_percentage(),
            'downloaded_pieces': len(self.piece_manager.completed_pieces),
            'total_pieces': self.total_pieces,
            'connected_peers': len(self.peer_connections),
            'download_speed': self.download_speed,
            'upload_speed': self.upload_speed
        }
    
    def pause_download(self) -> bool:
        """Pause the download"""
        with self.lock:
            if self.is_downloading and not self.is_paused:
                self.is_paused = True
                print("📴 Download paused")
                return True
            return False
    
    def resume_download(self) -> bool:
        """Resume the download"""
        with self.lock:
            if self.is_downloading and self.is_paused:
                self.is_paused = False
                print("▶️ Download resumed")
                return True
            return False
    
    def is_download_paused(self) -> bool:
        """Check if download is paused"""
        return self.is_paused
    
    def get_download_status(self) -> str:
        """Get current download status"""
        if not self.is_downloading:
            return "Stopped"
        elif self.is_paused:
            return "Paused"
        elif self.piece_manager.is_complete():
            return "Completed"
        else:
            return "Downloading"
    
    def stop_download(self) -> bool:
        """Stop the download completely"""
        with self.lock:
            if self.is_downloading:
                self.is_downloading = False
                self.is_paused = False
                
                # Close all peer connections
                for peer_addr, protocol in self.peer_connections.items():
                    try:
                        protocol.disconnect()
                    except Exception as e:
                        print(f"Error disconnecting from {peer_addr}: {e}")
                
                self.peer_connections.clear()
                print("🛑 Download stopped")
                return True
            return False
