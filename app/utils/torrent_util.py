from fastapi import UploadFile
from app.core.splitter_config import PIECE_SIZE
from app.core.config import settings
from pathlib import Path
from app.core.config import UPLOAD_DIR, TORRENT_DIR  
from app.utils.upload_util import gen_unique_name
from app.utils.splitter_util import split_file
from app.utils.hash_util import hash_pieces
import json


def gen_torrent(file: UploadFile, _uuid: str) -> Path: 
        """
        Generation d'un fichier .torrent
        """
        
        unique_name = gen_unique_name(file, _uuid)
        file_path = UPLOAD_DIR / unique_name

        pieces = split_file(str(file_path))
        hashes = hash_pieces(pieces)

        metadata = generate_metadata(
            file_name=file.filename,
            file_size=file_path.stat().st_size,
            piece_size=PIECE_SIZE,  
            piece_hashes=hashes,
            tracker_url=settings.TRACKER_URL
        )

        return save_metadata_file(metadata, str(_uuid))

    
def generate_metadata(file_name: str,file_size: int, piece_size: int,piece_hashes: list[str],tracker_url: str) -> dict:
    """
    Génère les métadonnées au format .torrent-like.
    """
    return {
        "file_name": file_name,
        "file_size": file_size,
        "piece_size": piece_size,
        "num_pieces": len(piece_hashes),
        "piece_hashes": piece_hashes,
        "tracker_url": tracker_url
    }

def save_metadata_file(metadata: dict, _uuid: str, output_dir: Path = TORRENT_DIR) -> Path:
    """
    Sauvegarde les métadonnées dans un fichier .torrent.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = _uuid + ".torrent"
    file_path = output_dir / file_name

    with open(file_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return file_path