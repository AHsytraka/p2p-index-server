import os
import hashlib
from typing import List, Dict, Any

class FileManager:
    """Handles file operations for P2P sharing"""
    
    @staticmethod
    def chunk_file(file_path: str, chunk_size: int = 2**18) -> List[bytes]:
        """Split file into chunks and return list of chunks"""
        chunks = []
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
        
        return chunks
    
    @staticmethod
    def verify_chunk_integrity(chunk_data: bytes, expected_hash: str) -> bool:
        """Verify the integrity of a chunk using SHA-1 hash"""
        actual_hash = hashlib.sha1(chunk_data).hexdigest()
        return actual_hash == expected_hash
    
    @staticmethod
    def reconstruct_file(chunks: List[bytes], output_path: str) -> bool:
        """Reconstruct file from chunks"""
        try:
            # Create directory if it doesn't exist and path has a directory part
            dir_path = os.path.dirname(output_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            print(f"📝 Writing file to: {output_path}")
            print(f"📏 Total chunks: {len(chunks)}")
            total_size = sum(len(chunk) for chunk in chunks)
            print(f"📐 Total size: {total_size} bytes")
            
            with open(output_path, 'wb') as f:
                for i, chunk in enumerate(chunks):
                    f.write(chunk)
                    if i % 100 == 0:  # Log progress every 100 chunks
                        print(f"📝 Written chunk {i}/{len(chunks)}")
            
            # Verify file was created
            if os.path.exists(output_path):
                actual_size = os.path.getsize(output_path)
                print(f"✅ File created successfully: {output_path}")
                print(f"📐 Final file size: {actual_size} bytes")
                return True
            else:
                print(f"❌ File was not created: {output_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error reconstructing file: {e}")
            print(f"📂 Attempted path: {output_path}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get file information"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = os.stat(file_path)
        return {
            'name': os.path.basename(file_path),
            'size': stat.st_size,
            'path': file_path,
            'created': stat.st_ctime,
            'modified': stat.st_mtime
        }
    
    @staticmethod
    def create_download_directory(base_path: str, torrent_name: str) -> str:
        """Create directory for downloading files"""
        download_dir = os.path.join(base_path, 'downloads', torrent_name)
        os.makedirs(download_dir, exist_ok=True)
        return download_dir
