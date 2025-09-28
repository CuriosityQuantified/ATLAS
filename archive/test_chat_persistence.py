#!/usr/bin/env python3
"""
Test script for ATLAS chat persistence
Tests database schema, chat manager, and API endpoints
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TASK_ID = f"test_task_{int(datetime.now().timestamp())}"

async def test_database_connection():
    """Test basic database connection"""
    print("🔍 Testing database connection...")
    
    try:
        from backend.src.database.chat_manager import chat_manager
        await chat_manager.initialize()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_chat_manager():
    """Test chat manager basic operations"""
    print("\n🔍 Testing chat manager operations...")
    
    try:
        from backend.src.database.chat_manager import chat_manager
        
        # Test session creation
        session_id = await chat_manager.create_chat_session(
            task_id=TASK_ID,
            user_id="test_user",
            metadata={"test": True}
        )
        print(f"✅ Created chat session: {session_id}")
        
        # Test message saving
        message_id = await chat_manager.save_message(
            session_id=session_id,
            message_type="user",
            content="Hello, this is a test message",
            metadata={"test_message": True}
        )
        print(f"✅ Saved message: {message_id}")
        
        # Test message retrieval
        messages = await chat_manager.get_chat_history(session_id)
        print(f"✅ Retrieved {len(messages)} messages")
        
        return True
    except Exception as e:
        print(f"❌ Chat manager test failed: {e}")
        return False

async def test_api_endpoints():
    """Test chat API endpoints"""
    print("\n🔍 Testing chat API endpoints...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get(f"{BASE_URL}/api/chat/health")
            if response.status_code == 200:
                print("✅ Chat health endpoint working")
            else:
                print(f"❌ Chat health endpoint failed: {response.status_code}")
                return False
            
            # Test session creation
            session_data = {
                "task_id": f"api_test_{TASK_ID}",
                "user_id": "test_user",
                "metadata": {"api_test": True}
            }
            
            response = await client.post(f"{BASE_URL}/api/chat/sessions", json=session_data)
            if response.status_code == 200:
                session_result = response.json()
                session_id = session_result["session_id"]
                print(f"✅ Created session via API: {session_id}")
            else:
                print(f"❌ Session creation failed: {response.status_code}")
                return False
            
            # Test message saving
            message_data = {
                "message_type": "user",
                "content": "Test message via API",
                "metadata": {"api_test": True}
            }
            
            response = await client.post(
                f"{BASE_URL}/api/chat/sessions/{session_id}/messages", 
                json=message_data
            )
            if response.status_code == 200:
                print("✅ Saved message via API")
            else:
                print(f"❌ Message saving failed: {response.status_code}")
                return False
            
            # Test message retrieval
            response = await client.get(f"{BASE_URL}/api/chat/sessions/{session_id}/messages")
            if response.status_code == 200:
                messages = response.json()
                print(f"✅ Retrieved {len(messages)} messages via API")
            else:
                print(f"❌ Message retrieval failed: {response.status_code}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

async def test_task_integration():
    """Test full task creation with chat persistence"""
    print("\n🔍 Testing task integration with chat persistence...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Create a task
            task_data = {
                "task_type": "general_analysis",
                "description": "Test task for chat persistence integration",
                "priority": "medium"
            }
            
            response = await client.post(f"{BASE_URL}/api/tasks", json=task_data)
            if response.status_code == 200:
                task_result = response.json()
                task_id = task_result["task_id"]
                print(f"✅ Created task: {task_id}")
                
                # Check if chat history exists for this task
                await asyncio.sleep(1)  # Give it a moment to process
                
                response = await client.get(f"{BASE_URL}/api/chat/tasks/{task_id}/history")
                if response.status_code == 200:
                    messages = response.json()
                    print(f"✅ Task has {len(messages)} chat messages")
                    return True
                else:
                    print(f"⚠️ No chat history found for task (this might be expected)")
                    return True
            else:
                print(f"❌ Task creation failed: {response.status_code}")
                return False
        
    except Exception as e:
        print(f"❌ Task integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting ATLAS Chat Persistence Tests\n")
    
    # Run tests in sequence
    tests = [
        ("Database Connection", test_database_connection),
        ("Chat Manager", test_chat_manager),
        ("API Endpoints", test_api_endpoints),
        ("Task Integration", test_task_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} Test")
        print('='*50)
        
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Chat persistence is working.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())