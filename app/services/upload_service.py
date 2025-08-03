from fastapi import Depends,APIRouter, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from pathlib import Path
from app.core.config import UPLOAD_DIR, DANGEROUS_CONTENT_TYPES, TORRENT_DIR  
from posixpath import basename
from app.models.data_mapping import DataMapping
from app.utils.splitter_util import split_file
from app.utils.hash_util import hash_pieces
from app.core.config import settings
import uuid
import shutil
import json


class UploadService:

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

        # Création les dossiers s'ils n'existent pas encore

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        TORRENT_DIR.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file: UploadFile = File(...)):
        """
        Téléverse un fichier après avoir validé son type MIME,
        puis le sauvegarde sur le disque.
        """
        self.validate_file(file)
        _uuid = self.save_file(file)      

        # Construction du chemin complet vers le fichier sauvegardé
        unique_name = self.gen_unique_name(file, _uuid)
        file_path = UPLOAD_DIR / unique_name

        # 1. Découpage
        pieces = split_file(str(file_path))  # retourne list[bytes]

        # 2. Calcul des hash
        hashes = hash_pieces(pieces)

        # 3. Génération des métadonnées
        metadata = self.generate_metadata(
            file_name=file.filename,
            file_size=file_path.stat().st_size,
            piece_size=1048576,  
            piece_hashes=hashes,
            tracker_url=settings.TRACKER_URL
        )

        # 4. Sauvegarde du fichier .torrent
        torrent_path = self.save_metadata_file(metadata)

        return {
            "message": "Fichier reçu avec succès",
            "filename": file.filename,
            "uuid": str(_uuid),
            "torrent_file": torrent_path.name  # nom du fichier .torrent généré
        }

    def validate_file(self, file: UploadFile):
        """
        Vérifie le type et le contenu du fichier
        """
        self.validate_mime(file)
        self.validate_not_null_content_file(file)
        
        
    def validate_mime(self, file: UploadFile):
        """
        Vérifie si le type MIME du fichier fait partie des types interdits.
        """
        if file.content_type in DANGEROUS_CONTENT_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Type de fichier interdit : {file.content_type}"
            )

    def validate_not_null_content_file(seilf, file: UploadFile) :
        """
        Vérifie si le fichier est vide
        """
        file.file.seek(0, 2) 
        size = file.file.tell()
        file.file.seek(0)    
        if size == 0:
            raise HTTPException(
                status_code=400,
                detail="Fichier vide non autorisé."
            )

    def save_file(self, file: UploadFile) -> str:
        """
        Copie le contenu du fichier reçu dans le répertoire de téléchargement et enregistre le mapping dans la base de donnée
        """
        _uuid = uuid.uuid4()
        unique_name = self.gen_unique_name(file, _uuid)
        file_path = UPLOAD_DIR / unique_name

        self.write_file_to_disk(file, file_path)
        self.save_map_file(str(_uuid), file.filename, unique_name)

        return _uuid

    def write_file_to_disk(self, file: UploadFile, file_path: str):
        """
        Copie le fichier dans la disque dure
        """
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la sauvegarde du fichier : {str(e)}"
            )

    def gen_unique_name(self, file: UploadFile, _uuid: uuid)-> str :
        """
        Genere un nom unique avec un UUID pour eviter les collisons de nom des fichiers
        """
        filename = basename(file.filename)
        suffix = Path(filename).suffix

        return f"{_uuid}{suffix}"

    def save_map_file(self, _uuid: str, orginal_name: str, storage_name: str):
        """
        Sauvegarde l'information sur les noms du fichier dans la base de donnée
        """
        new_file = DataMapping(
            uuid=_uuid,
            original_name=orginal_name,
            storage_name=storage_name
        )

        self.db.add(new_file)
        self.db.commit()
    
    def generate_metadata(self, file_name: str,file_size: int, piece_size: int,piece_hashes: list[str],tracker_url: str) -> dict:
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
    
    def save_metadata_file(self, metadata: dict, output_dir: Path = TORRENT_DIR) -> Path:
        """
        Sauvegarde les métadonnées dans un fichier .torrent.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        file_name = metadata["file_name"] + ".torrent"
        file_path = output_dir / file_name

        with open(file_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return file_path