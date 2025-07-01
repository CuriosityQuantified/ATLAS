#!/usr/bin/env python3
"""
Integration test for AG-UI real-time communication between demo agent and backend server
"""

import asyncio
import websockets
import json
import time
from typing import Dict, Any

async def test_websocket_connection():
    """Test WebSocket connection to backend AG-UI server"""
    task_id = f"integration_test_{int(time.time())}"
    ws_url = f"ws://localhost:8000/api/agui/ws/{task_id}"
    
    print(f"🔗 Testing WebSocket connection to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connection established")
            
            # Send a test message
            test_message = {
                "type": "user_input",
                "data": {
                    "content": "Hello from integration test",
                    "agent_id": "test_agent"
                }
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Sent test message")
            
            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Received: {response}")
                return True
            except asyncio.TimeoutError:
                print("⏰ No response received within timeout")
                return True  # Connection worked, just no response expected
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def test_sse_connection():
    """Test Server-Sent Events connection"""
    import httpx
    
    task_id = f"integration_test_{int(time.time())}"
    sse_url = f"http://localhost:8000/api/agui/stream/{task_id}"
    
    print(f"🔗 Testing SSE connection to: {sse_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", sse_url, timeout=5.0) as response:
                if response.status_code == 200:
                    print("✅ SSE connection established")
                    
                    # Read a few events
                    line_count = 0
                    async for line in response.aiter_lines():
                        if line.strip():
                            print(f"📥 SSE Event: {line[:100]}...")
                            line_count += 1
                            if line_count >= 3:  # Just read a few events
                                break
                    
                    return True
                else:
                    print(f"❌ SSE connection failed: HTTP {response.status_code}")
                    return False
                    
    except Exception as e:
        print(f"❌ SSE connection failed: {e}")
        return False

async def test_demo_agent_with_backend():
    """Test demo agent with backend server integration"""
    from src.agents.demo_agent import DemoAgent
    
    print("🤖 Testing demo agent with backend integration")
    
    # Create agent
    agent = DemoAgent(agent_id="integration_test_agent", name="Integration Test Agent")
    task_id = f"integration_test_{int(time.time())}"
    
    try:
        # Run a simple conversation
        result = await agent.process_task(
            task_id,
            "Hello! This is an integration test. Please respond briefly."
        )
        
        if result["success"]:
            print("✅ Demo agent completed successfully")
            print(f"📊 Response: {result['response'][:100]}...")
            print(f"💰 Cost: ${result['metadata']['cost']:.6f}")
            print(f"⏱️  Time: {result['metadata']['processing_time']:.2f}s")
            return True
        else:
            print(f"❌ Demo agent failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Demo agent error: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 Starting ATLAS AG-UI Integration Tests")
    print("=" * 50)
    
    results = {}
    
    # Test 1: WebSocket connection
    print("\n📡 Test 1: WebSocket Connection")
    results["websocket"] = await test_websocket_connection()
    
    # Test 2: SSE connection  
    print("\n📡 Test 2: Server-Sent Events")
    results["sse"] = await test_sse_connection()
    
    # Test 3: Demo agent integration
    print("\n🤖 Test 3: Demo Agent Integration")
    results["demo_agent"] = await test_demo_agent_with_backend()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.upper()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All integration tests PASSED!")
        return True
    else:
        print("⚠️  Some integration tests FAILED!")
        return False

if __name__ == "__main__":
    asyncio.run(main())