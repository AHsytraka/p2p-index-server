#!/usr/bin/env python3
"""
Test upload endpoint directly with requests
"""

import requests
import os

def test_upload():
    """Test the upload endpoint directly"""
    try:
        # Prepare test file
        test_file = "test_file.txt"
        if not os.path.exists(test_file):
            print(f"Test file {test_file} not found")
            return
        
        print(f"Testing upload of: {test_file}")
        
        # Upload file
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/plain')}
            response = requests.post(
                "http://localhost:8000/api/tracker/upload", 
                files=files,
                timeout=30
            )
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Torrent created:")
            print(f"  ID: {data['id']}")
            print(f"  Name: {data['name']}")
            print(f"  Info hash: {data['info_hash']}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Details: {response.text}")
    
    except Exception as e:
        print(f"Error during upload test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_upload()
