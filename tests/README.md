# Tests Directory

This directory contains test scripts for debugging and validating the P2P BitTorrent system.

## Test Files

### `test_database.py`
Tests database operations including torrent and peer management.

**Usage:**
```bash
python tests/test_database.py
```

### `test_torrent_creation.py`
Isolates and tests the torrent creation functionality.

**Usage:**
```bash
python tests/test_torrent_creation.py
```

### `test_upload.py`
Tests the upload endpoint directly with HTTP requests.

**Usage:**
```bash
python tests/test_upload.py
```

## Running Tests

All tests should be run from the project root directory:

```bash
cd p2p-index-server
python tests/test_database.py
python tests/test_torrent_creation.py
python tests/test_upload.py
```

## Notes

- Make sure the backend server is running before running tests
- These tests help isolate issues during development
- Test files create temporary data for validation
