"""
Test script to verify the FastAPI endpoint is working correctly.
"""
import requests
import json
import time

def test_api():
    base_url = "http://localhost:8000"
    
    print("Testing FastAPI endpoints...")
    
    # Test basic endpoint
    try:
        response = requests.get(f"{base_url}/api/test")
        print(f"✓ Test endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Test endpoint failed: {e}")
        return
    
    # Test chat start
    try:
        response = requests.post(f"{base_url}/api/chat/start")
        print(f"✓ Chat start: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Chat start failed: {e}")
        return
    
    # Test chat message
    try:
        payload = {
            "userInput": "Hello, how are you?",
            "chatHistory": [],
            "memory": ""
        }
        
        print(f"Sending payload: {payload}")
        response = requests.post(f"{base_url}/api/chat/message", json=payload, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Chat message successful:")
            print(f"  Response text: {data.get('response_text', 'None')}")
            print(f"  Audio file path: {data.get('audio_file_path', 'None')}")
            print(f"  Memory: {data.get('memory', 'None')}")
        else:
            print(f"✗ Chat message failed: {response.status_code}")
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Chat message failed: {e}")

if __name__ == "__main__":
    test_api()
