import socket
import struct
import threading
import json
from typing import Dict, Any, Callable, Optional
from enum import IntEnum

class MessageType(IntEnum):
    HANDSHAKE = 0
    CHOKE = 1
    UNCHOKE = 2
    INTERESTED = 3
    NOT_INTERESTED = 4
    HAVE = 5
    BITFIELD = 6
    REQUEST = 7
    PIECE = 8
    CANCEL = 9
    KEEP_ALIVE = 255  # Special value for keep-alive messages

class P2PProtocol:
    """Handles P2P communication protocol between peers"""
    
    PROTOCOL_NAME = b"P2P-BitTorrent-Python"
    
    def __init__(self, peer_id: str, info_hash: str):
        self.peer_id = peer_id.encode('utf-8')[:20]  # Ensure 20 bytes
        self.info_hash = info_hash.encode('utf-8')[:20]  # Ensure 20 bytes
        self.socket: Optional[socket.socket] = None
        self.connected_peer_id: Optional[bytes] = None
        
    def create_handshake_message(self) -> bytes:
        """Create handshake message"""
        protocol_name = self.PROTOCOL_NAME
        protocol_length = len(protocol_name)
        reserved = b'\x00' * 8  # 8 reserved bytes
        
        handshake = struct.pack(
            f'!B{protocol_length}s8s20s20s',
            protocol_length,
            protocol_name,
            reserved,
            self.info_hash,
            self.peer_id
        )
        return handshake
    
    def parse_handshake_message(self, data: bytes) -> Dict[str, Any]:
        """Parse received handshake message"""
        if len(data) < 49:  # Minimum handshake size
            raise ValueError("Invalid handshake message length")
        
        protocol_length = struct.unpack('!B', data[0:1])[0]
        protocol_name = data[1:1+protocol_length]
        reserved = data[1+protocol_length:9+protocol_length]
        info_hash = data[9+protocol_length:29+protocol_length]
        peer_id = data[29+protocol_length:49+protocol_length]
        
        return {
            'protocol_name': protocol_name,
            'reserved': reserved,
            'info_hash': info_hash,
            'peer_id': peer_id
        }
    
    def create_message(self, message_type: MessageType, payload: bytes = b'') -> bytes:
        """Create a protocol message"""
        length = len(payload) + 1  # +1 for message type
        message = struct.pack('!IB', length, message_type) + payload
        return message
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse received message"""
        if len(data) < 4:
            raise ValueError("Message too short")
        
        length = struct.unpack('!I', data[0:4])[0]
        
        if length == 0:
            return {'type': 'keep_alive', 'payload': b''}
        
        if len(data) < 4 + length:
            raise ValueError("Incomplete message")
        
        message_type = struct.unpack('!B', data[4:5])[0]
        payload = data[5:4+length]
        
        return {
            'type': MessageType(message_type),
            'payload': payload,
            'length': length
        }
    
    def connect_to_peer(self, ip: str, port: int) -> bool:
        """Connect to a peer"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Reduced timeout for initial connection
            self.socket.connect((ip, port))
            
            # Send handshake
            handshake = self.create_handshake_message()
            self.socket.send(handshake)
            
            # Receive handshake response
            response = self.socket.recv(1024)
            handshake_data = self.parse_handshake_message(response)
            
            # Verify info hash matches
            if handshake_data['info_hash'] != self.info_hash:
                raise ValueError("Info hash mismatch")
            
            self.connected_peer_id = handshake_data['peer_id']
            
            # Set timeout for message operations
            self.socket.settimeout(5.0)  # 5 second timeout for messages
            return True
            
        except Exception as e:
            print(f"Failed to connect to peer {ip}:{port}: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def send_message(self, message_type: MessageType, payload: bytes = b'') -> bool:
        """Send a message to connected peer"""
        if not self.socket:
            return False
        
        try:
            message = self.create_message(message_type, payload)
            self.socket.send(message)
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from connected peer"""
        if not self.socket:
            return None
        
        try:
            # Receive message length first
            length_data = self._recv_exact(4)
            if not length_data:
                return None
            
            length = struct.unpack('!I', length_data)[0]
            
            if length == 0:
                return {'type': 'keep_alive', 'payload': b''}
            
            # Receive the rest of the message
            message_data = self._recv_exact(length)
            if not message_data:
                return None
            
            full_message = length_data + message_data
            return self.parse_message(full_message)
            
        except socket.timeout:
            print("Failed to receive message: timed out")
            return None
        except Exception as e:
            print(f"Failed to receive message: {e}")
            return None
    
    def _recv_exact(self, size: int) -> Optional[bytes]:
        """Receive exact number of bytes from socket"""
        data = b''
        while len(data) < size:
            try:
                chunk = self.socket.recv(size - len(data))
                if not chunk:
                    return None  # Connection closed
                data += chunk
            except socket.timeout:
                return None
            except Exception:
                return None
        return data
    
    def disconnect(self):
        """Disconnect from peer"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected_peer_id = None
