from pathlib import Path

def split_file(file_path: str, piece_size: int = 1048576) -> list[bytes]:
    """
    Découpe le fichier `file_path` en morceaux de taille `piece_size`.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {file_path}")
    if not path.is_file():
        raise ValueError(f"Le chemin n'est pas un fichier : {file_path}")

    pieces = []
    try:
        with path.open("rb") as f:
            while chunk := f.read(piece_size):
                pieces.append(chunk)
    except Exception as e:
        raise IOError(f"Erreur lors de la lecture du fichier : {e}")

    return pieces