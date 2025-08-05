#!/usr/bin/env python3
"""
Test peer ID generation consistency
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.bittorrent import BitTorrentUtils

# Test consistent peer ID generation
info_hash = "1fa7019dd81cbcded18797a8d7da5c220337fbe1"  # Example from recent download
ip_address = "192.168.175.242"

print("Testing consistent peer ID generation:")
print(f"Info Hash: {info_hash}")
print(f"IP Address: {ip_address}")
print()

# Generate peer IDs multiple times with same input
for i in range(5):
    seeder_id = BitTorrentUtils.generate_peer_id("P2PS", info_hash, ip_address)
    downloader_id = BitTorrentUtils.generate_peer_id("P2PD", info_hash, ip_address)
    print(f"Test {i+1}:")
    print(f"  Seeder ID:     {seeder_id}")
    print(f"  Downloader ID: {downloader_id}")

print()
print("Testing different info hash:")
different_hash = "abc123def456789012345678901234567890abcd"
for i in range(3):
    seeder_id = BitTorrentUtils.generate_peer_id("P2PS", different_hash, ip_address)
    downloader_id = BitTorrentUtils.generate_peer_id("P2PD", different_hash, ip_address)
    print(f"Different hash {i+1}:")
    print(f"  Seeder ID:     {seeder_id}")
    print(f"  Downloader ID: {downloader_id}")

print()
print("Testing different IP:")
different_ip = "10.0.0.1"
for i in range(3):
    seeder_id = BitTorrentUtils.generate_peer_id("P2PS", info_hash, different_ip)
    downloader_id = BitTorrentUtils.generate_peer_id("P2PD", info_hash, different_ip)
    print(f"Different IP {i+1}:")
    print(f"  Seeder ID:     {seeder_id}")
    print(f"  Downloader ID: {downloader_id}")
