from fastapi import UploadFile, HTTPException
from app.core.config import DANGEROUS_CONTENT_TYPES

def validate_file(file: UploadFile):
        """
        Vérifie le type et le contenu du fichier
        """
        validate_mime(file)
        validate_not_null_content_file(file)
    
def validate_mime(file: UploadFile):
    """
    Vérifie si le type MIME du fichier fait partie des types interdits.
    """
    if file.content_type in DANGEROUS_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Type de fichier interdit : {file.content_type}"
        )

def validate_not_null_content_file(file: UploadFile) :
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
        