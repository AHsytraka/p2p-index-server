from fastapi import UploadFile
import uuid
from pathlib import Path
from posixpath import basename

def gen_unique_name(file: UploadFile, _uuid: uuid)-> str :
        """
        Genere un nom unique avec un UUID pour eviter les collisons de nom des fichiers
        """
        filename = basename(file.filename)
        suffix = Path(filename).suffix

        return f"{_uuid}{suffix}"