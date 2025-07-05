#!/usr/bin/env python3
"""
Final comprehensive test for ATLAS chat persistence
Tests complete end-to-end functionality with real task creation and chat history
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"

async def test_complete_chat_flow():
    """Test complete chat persistence flow"""
    print("🚀 Testing Complete Chat Persistence Flow")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Step 1: Create a task
        print("\n📝 Step 1: Creating a new task...")
        task_data = {
            "task_type": "general_analysis",
            "description": "Complete test of chat persistence functionality with detailed conversation history",
            "priority": "high"
        }
        
        response = await client.post(f"{BASE_URL}/api/tasks", json=task_data)
        if response.status_code != 200:
            print(f"❌ Task creation failed: {response.status_code}")
            return False
            
        task_result = response.json()
        task_id = task_result["task_id"]
        print(f"✅ Task created: {task_id}")
        
        # Step 2: Start the task
        print(f"\n🚀 Step 2: Starting task {task_id}...")
        response = await client.post(f"{BASE_URL}/api/tasks/{task_id}/start")
        if response.status_code != 200:
            print(f"❌ Task start failed: {response.status_code}")
            return False
            
        print("✅ Task started successfully")
        
        # Step 3: Wait for task processing
        print("\n⏳ Step 3: Waiting for task completion...")
        await asyncio.sleep(12)  # Give the agent time to process
        
        # Step 4: Check chat history
        print(f"\n💬 Step 4: Checking chat history for task {task_id}...")
        response = await client.get(f"{BASE_URL}/api/chat/tasks/{task_id}/history")
        if response.status_code != 200:
            print(f"❌ Chat history retrieval failed: {response.status_code}")
            return False
            
        chat_history = response.json()
        print(f"✅ Retrieved {len(chat_history)} messages from chat history")
        
        # Step 5: Analyze chat history
        print("\n🔍 Step 5: Analyzing chat history...")
        user_messages = [msg for msg in chat_history if msg['message_type'] == 'user']
        agent_messages = [msg for msg in chat_history if msg['message_type'] == 'agent']
        system_messages = [msg for msg in chat_history if msg['message_type'] == 'system']
        
        print(f"   • User messages: {len(user_messages)}")
        print(f"   • Agent messages: {len(agent_messages)}")
        print(f"   • System messages: {len(system_messages)}")
        
        if len(user_messages) == 0:
            print("❌ No user messages found in chat history")
            return False
            
        if len(agent_messages) == 0:
            print("❌ No agent messages found in chat history")
            return False
            
        # Step 6: Check recent sessions
        print(f"\n📋 Step 6: Checking recent sessions...")
        response = await client.get(f"{BASE_URL}/api/chat/recent?limit=10")
        if response.status_code != 200:
            print(f"❌ Recent sessions retrieval failed: {response.status_code}")
            return False
            
        recent_sessions = response.json()
        print(f"✅ Found {len(recent_sessions)} recent chat sessions")
        
        # Find our session
        our_session = next((s for s in recent_sessions if s['task_id'] == task_id), None)
        if not our_session:
            print(f"❌ Our task {task_id} not found in recent sessions")
            return False
            
        print(f"✅ Our session found with {our_session['message_count']} messages")
        
        # Step 7: Display conversation summary
        print(f"\n📄 Step 7: Conversation Summary")
        print("-" * 40)
        
        for i, message in enumerate(chat_history[:5]):  # Show first 5 messages
            timestamp = datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
            msg_type = message['message_type'].upper()
            content_preview = message['content'][:100] + "..." if len(message['content']) > 100 else message['content']
            
            print(f"{i+1}. [{timestamp.strftime('%H:%M:%S')}] {msg_type}: {content_preview}")
            
        if len(chat_history) > 5:
            print(f"   ... and {len(chat_history) - 5} more messages")
            
        # Step 8: Verify MLflow tracking (if available)
        print(f"\n📊 Step 8: Checking MLflow integration...")
        
        # Check if we have MLflow run ID in task data
        response = await client.get(f"{BASE_URL}/api/tasks/{task_id}")
        if response.status_code == 200:
            task_status = response.json()
            print("✅ Task status retrieved successfully")
            
            # Look for MLflow info in agent messages
            agent_msg_with_mlflow = next((msg for msg in agent_messages if 'mlflow' in str(msg.get('metadata', {})).lower()), None)
            if agent_msg_with_mlflow:
                print("✅ MLflow tracking information found in message metadata")
            else:
                print("ℹ️ No MLflow tracking information found (may be expected)")
        
        # Final verification
        print(f"\n✅ Complete Chat Persistence Test PASSED!")
        print("=" * 60)
        print("Summary:")
        print(f"  • Task ID: {task_id}")
        print(f"  • Total messages: {len(chat_history)}")
        print(f"  • User messages: {len(user_messages)}")
        print(f"  • Agent messages: {len(agent_messages)}")
        print(f"  • Session found in recent list: {'Yes' if our_session else 'No'}")
        print(f"  • Message count in session: {our_session['message_count'] if our_session else 'N/A'}")
        
        return True

async def main():
    """Run the complete test"""
    try:
        success = await test_complete_chat_flow()
        
        if success:
            print("\n🎉 All tests PASSED! Chat persistence is fully functional.")
            print("\n🔗 You can now:")
            print("  1. Visit http://localhost:3002/tasks")
            print("  2. Select 'New Task' from the dropdown")
            print("  3. Create a task and see it save to chat history")
            print("  4. Reload the page and see the conversation history persist")
            print("  5. Select previous conversations from the dropdown")
        else:
            print("\n⚠️ Some tests failed. Check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Test crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())