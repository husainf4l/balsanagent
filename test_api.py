#!/usr/bin/env python3
"""
Test script for the FastAPI chat agent
Run this after starting the FastAPI server to test the endpoints
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_create_session():
    """Test creating a new session"""
    print("\nTesting session creation...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/sessions")
        if response.status_code == 200:
            session_data = response.json()
            print("✅ Session created successfully")
            print(f"Session ID: {session_data['session_id']}")
            return session_data['session_id']
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return None

def test_chat_message(session_id, message):
    """Test sending a chat message"""
    print(f"\nTesting chat message: '{message}'...")
    try:
        payload = {
            "message": message,
            "session_id": session_id
        }
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Chat message sent successfully")
            print(f"Response: {chat_response['response'][:200]}...")
            if chat_response.get('error'):
                print(f"⚠️  Error in response: {chat_response['error']}")
            return True
        else:
            print(f"❌ Chat message failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat message error: {e}")
        return False

def test_chat_history(session_id):
    """Test getting chat history"""
    print(f"\nTesting chat history for session {session_id}...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/sessions/{session_id}/history")
        if response.status_code == 200:
            history_data = response.json()
            print("✅ Chat history retrieved successfully")
            print(f"History entries: {len(history_data['history'])}")
            for i, entry in enumerate(history_data['history'][-3:]):  # Show last 3 entries
                print(f"  {i+1}. {entry['role']}: {entry['content'][:100]}...")
            return True
        else:
            print(f"❌ Chat history failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat history error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting FastAPI Chat Agent Tests")
    print("=" * 50)
    
    # Test health check
    test_health_check()
    
    # Test session creation
    session_id = test_create_session()
    if not session_id:
        print("❌ Cannot continue without session ID")
        return
    
    # Wait a bit
    time.sleep(1)
    
    # Test chat messages
    test_messages = [
        "Hello, can you help me analyze my business data?",
        "What tables are available in the database?",
        "Show me the top 5 customers by sales volume"
    ]
    
    for message in test_messages:
        success = test_chat_message(session_id, message)
        if success:
            time.sleep(2)  # Wait between messages
        else:
            print("⚠️  Continuing despite chat error...")
    
    # Test chat history
    test_chat_history(session_id)
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    main()
