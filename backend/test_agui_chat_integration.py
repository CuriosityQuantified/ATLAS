#!/usr/bin/env python3
"""
Test script for AG-UI chat integration with immediate message display
Tests the new chat endpoints and WebSocket broadcasting
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"

async def test_chat_integration():
    """Test complete chat flow with AG-UI broadcasting"""
    
    print("🚀 Starting AG-UI Chat Integration Test")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 1. Create a new task
        print("\n1️⃣ Creating new task...")
        task_data = {
            "task_type": "general_analysis",
            "description": "Test the new responsive chat system",
            "priority": "medium",
            "context": {}
        }
        
        async with session.post(f"{API_BASE}/api/tasks", json=task_data) as resp:
            if resp.status != 200:
                print(f"❌ Failed to create task: {resp.status}")
                return
            
            task_response = await resp.json()
            task_id = task_response["task_id"]
            print(f"✅ Task created: {task_id}")
        
        # 2. Connect to WebSocket
        print(f"\n2️⃣ Connecting to WebSocket for task {task_id}...")
        ws_url = f"{WS_BASE}/api/agui/ws/{task_id}"
        
        try:
            async with session.ws_connect(ws_url) as ws:
                print("✅ WebSocket connected")
                
                # 3. Send a user message via the new chat endpoint
                print("\n3️⃣ Sending user message via chat API...")
                message_data = {
                    "message_type": "user",
                    "content": "Hello, can you help me analyze market trends?",
                    "metadata": {
                        "task_id": task_id,
                        "user_id": "test_user"
                    }
                }
                
                async with session.post(
                    f"{API_BASE}/api/chat/{task_id}/message", 
                    json=message_data
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to send message: {resp.status}")
                        error_detail = await resp.text()
                        print(f"Error: {error_detail}")
                    else:
                        result = await resp.json()
                        print(f"✅ Message sent: {result}")
                
                # 4. Listen for WebSocket broadcasts
                print("\n4️⃣ Listening for WebSocket messages...")
                message_count = 0
                timeout = 10  # seconds
                
                try:
                    async with asyncio.timeout(timeout):
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                message_count += 1
                                
                                print(f"\n📨 WebSocket Message #{message_count}:")
                                print(f"   Event Type: {data.get('event_type')}")
                                print(f"   Agent ID: {data.get('agent_id', 'N/A')}")
                                
                                if data.get('event_type') == 'agent_dialogue_update':
                                    content = data.get('data', {}).get('content', {})
                                    print(f"   Direction: {data.get('data', {}).get('direction')}")
                                    print(f"   Content: {content.get('data', 'N/A')[:100]}...")
                                
                                # Stop after receiving a few messages
                                if message_count >= 5:
                                    break
                                    
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                print(f"❌ WebSocket error: {ws.exception()}")
                                break
                                
                except asyncio.TimeoutError:
                    print(f"\n⏱️ Timeout after {timeout} seconds")
                
                # 5. Test agent message broadcast
                print("\n5️⃣ Simulating agent response...")
                agent_message = {
                    "message_type": "agent",
                    "content": "I'd be happy to help you analyze market trends. Let me gather the latest data for you.",
                    "agent_id": "global_supervisor",
                    "metadata": {
                        "task_id": task_id,
                        "processing_time_ms": 1500
                    }
                }
                
                async with session.post(
                    f"{API_BASE}/api/chat/{task_id}/message", 
                    json=agent_message
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to send agent message: {resp.status}")
                    else:
                        result = await resp.json()
                        print(f"✅ Agent message sent: {result}")
                
                # 6. Verify chat history
                print("\n6️⃣ Retrieving chat history...")
                async with session.get(
                    f"{API_BASE}/api/chat/tasks/{task_id}/history"
                ) as resp:
                    if resp.status == 200:
                        messages = await resp.json()
                        print(f"✅ Found {len(messages)} messages in history")
                        for msg in messages:
                            print(f"   - {msg['message_type']}: {msg['content'][:50]}...")
                    else:
                        print(f"❌ Failed to get chat history: {resp.status}")
                
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    print("\n" + "=" * 50)
    print("✨ Test completed!")

async def test_typing_indicators():
    """Test agent typing indicators"""
    print("\n🔤 Testing Typing Indicators")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Create a task first
        task_data = {
            "task_type": "general_analysis",
            "description": "Test typing indicators",
            "priority": "medium"
        }
        
        async with session.post(f"{API_BASE}/api/tasks", json=task_data) as resp:
            task_response = await resp.json()
            task_id = task_response["task_id"]
            print(f"✅ Task created: {task_id}")
        
        # Connect to WebSocket and simulate agent status changes
        ws_url = f"{WS_BASE}/api/agui/ws/{task_id}"
        
        async with session.ws_connect(ws_url) as ws:
            print("✅ WebSocket connected")
            
            # Simulate typing status via the simulate endpoint
            print("\n📝 Simulating agent typing...")
            simulation_data = {
                "task_id": task_id,
                "agent_id": "global_supervisor"
            }
            
            async with session.post(
                f"{API_BASE}/api/dev/simulate-agent-activity",
                json=simulation_data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ Simulation triggered: {result}")
                else:
                    print(f"❌ Simulation failed: {resp.status}")

if __name__ == "__main__":
    print("🚀 ATLAS AG-UI Chat Integration Test Suite")
    print("Make sure the backend is running on http://localhost:8000")
    print()
    
    try:
        asyncio.run(test_chat_integration())
        asyncio.run(test_typing_indicators())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")