"""
Test script to verify static file serving is working.
"""

import os
import sys

import requests


def test_static_files():
    base_url = "http://localhost:8000"

    print("Testing static file serving...")

    # Check if audio file exists locally
    audio_path = "src/miramind/frontend/public/output.wav"
    if os.path.exists(audio_path):
        print(f"✓ Audio file exists locally: {audio_path}")
        print(f"  File size: {os.path.getsize(audio_path)} bytes")
    else:
        print(f"✗ Audio file not found locally: {audio_path}")
        return

    # Test static file access
    static_urls = [
        f"{base_url}/output.wav",
        f"{base_url}/api/audio/output.wav",
        f"{base_url}/static/output.wav",
    ]

    for url in static_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ Static file accessible: {url}")
                print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"  Content-Length: {response.headers.get('content-length', 'unknown')}")
            else:
                print(f"✗ Static file not accessible: {url} (status: {response.status_code})")
        except Exception as e:
            print(f"✗ Error accessing {url}: {e}")

    # Test if FastAPI is running
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ FastAPI server is running")
        else:
            print(f"✗ FastAPI server issue (status: {response.status_code})")
    except Exception as e:
        print(f"✗ FastAPI server not accessible: {e}")


if __name__ == "__main__":
    test_static_files()
