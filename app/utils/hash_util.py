import hashlib
from typing import List

def hash_pieces(pieces: List[bytes]) -> List[str]:
    return [hashlib.sha1(piece).hexdigest() for piece in pieces]
