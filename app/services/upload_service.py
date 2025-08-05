from fastapi import Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import UPLOAD_DIR, TORRENT_DIR  
from app.utils.upload_validation import validate_file
from app.utils.torrent_util import gen_torrent
from app.core.config import UPLOAD_DIR
from app.utils.upload_util import gen_unique_name
from app.models.data_mapping import DataMapping
import uuid
import shutil



class UploadService:

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

        # Créer les dossiers s'ils n'existent pas encore
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        TORRENT_DIR.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file: UploadFile = File(...)):
        """
        Téléverse un fichier après avoir validé son type MIME,
        puis le sauvegarde sur le disque et genere le fichier torrent.
        """
        validate_file(file)
        _uuid = self.save_file(file)      

        torrent_path = gen_torrent(file, _uuid)

        return {
            "message": "Fichier reçu avec succès",
            "filename": file.filename,
            "uuid": str(_uuid),
            "torrent_file": torrent_path.name 
        }

    def save_file(self, file: UploadFile) -> uuid.UUID:
        """
        Copie le contenu du fichier reçu dans le répertoire de téléchargement et enregistre le mapping dans la base de donnée
        """
        _uuid = uuid.uuid4()
        unique_name = gen_unique_name(file, _uuid)
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
  
    