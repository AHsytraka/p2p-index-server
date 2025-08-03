import pytest
from app.services.splitter_service import SplitterService
from pathlib import Path

splitter = SplitterService()

def setup_test_file(path: Path, size: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"A" * size)

def test_split_file_regular_case():
    file = Path("tests/data/05d2a2aa-0659-430b-9441-d741ad3aa212.mp4")
    setup_test_file(file, 3_000_000)  # 3 MB
    pieces = splitter.split_file(str(file), piece_size=1_000_000)
    assert len(pieces) == 3
    assert all(isinstance(p, bytes) for p in pieces)

def test_split_file_small_file():
    file = Path("tests/data/test_small.bin")
    setup_test_file(file, 100)  # 100 bytes
    pieces = splitter.split_file(str(file), piece_size=1024)
    assert len(pieces) == 1

def test_split_file_exact_multiple():
    file = Path("tests/data/test_exact.bin")
    setup_test_file(file, 2048)  # 2 KB
    pieces = splitter.split_file(str(file), piece_size=1024)
    assert len(pieces) == 2
    assert all(len(p) == 1024 for p in pieces)

def test_split_file_not_found():
    with pytest.raises(FileNotFoundError):
        splitter.split_file("tests/data/fichier_inexistant.bin")

def test_split_file_path_is_directory():
    dir_path = Path("tests/data/")
    with pytest.raises(ValueError):
        splitter.split_file(str(dir_path))
 