# Scripts Directory

This directory contains utility scripts for the P2P BitTorrent system.

## Scripts

### `auto_seeder.py`
Automatically registers your machine as a seeder for all torrents you have uploaded.
This solves the "no peers found" issue when testing on a single machine.

**Usage:**
```bash
python scripts/auto_seeder.py
```

### `simple_seeder.py`
A more advanced seeder that can serve file pieces to downloaders.
Used for P2P testing.

**Usage:**
```bash
python scripts/simple_seeder.py <torrent_file> <original_file>
```

### `client.py`
Command-line interface for the P2P system.
Provides CLI access to torrent creation and downloading.

**Usage:**
```bash
python scripts/client.py --help
```

## Notes

- Run these scripts from the project root directory
- Make sure the backend server is running before using these scripts
- The auto_seeder.py is particularly useful for single-machine testing
