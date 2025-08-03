from fastapi import Depends,APIRouter, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from pathlib import Path
from app.core.config import UPLOAD_DIR, DANGEROUS_CONTENT_TYPES  
from posixpath import basename
from app.models.data_mapping import DataMapping
import uuid
import shutil


class UploadService:

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

        # Création du dossier d'upload s'il n'existe pas encore
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file: UploadFile = File(...)):
        """
        Téléverse un fichier après avoir validé son type MIME,
        puis le sauvegarde sur le disque.
        """
        self.validate_file(file)
        _uuid = self.save_file(file)      

        return {
            "message": "Fichier reçu avec succès",
            "filename": file.filename, 
            "uuid": _uuid 
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