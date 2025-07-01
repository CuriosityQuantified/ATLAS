#!/usr/bin/env python3
"""
Test demo agent integration with backend server's shared AG-UI broadcaster
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

from src.agents.demo_agent import DemoAgent


async def get_shared_broadcaster():
    """Get the shared AG-UI broadcaster from the backend server"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/agui/broadcaster")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Shared broadcaster available: {data}")
                return data.get("has_connection_manager", False)
            else:
                print(f"❌ Failed to get broadcaster: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error getting broadcaster: {e}")
        return False


class ServerIntegratedDemoAgent(DemoAgent):
    """Demo agent that uses the server's shared AG-UI broadcaster"""
    
    def __init__(self, agent_id: str = "demo_agent", name: str = "Demo Agent"):
        super().__init__(agent_id, name)
        # We'll replace the broadcaster with the server's shared one
        self.shared_broadcaster_available = False
    
    async def initialize_with_server(self):
        """Initialize agent with server's shared broadcaster"""
        try:
            # Test if we can connect to the shared broadcaster
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/agui/broadcaster")
                if response.status_code == 200:
                    data = response.json()
                    self.shared_broadcaster_available = data.get("has_connection_manager", False)
                    if self.shared_broadcaster_available:
                        print("✅ Agent will use server's shared broadcaster with connection manager")
                    else:
                        print("⚠️  Server broadcaster available but no connection manager")
                    return True
                else:
                    print(f"❌ Cannot connect to server broadcaster: HTTP {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Failed to initialize with server: {e}")
            return False
    
    async def process_task_with_server_integration(self, task_id: str, user_input: str) -> Dict:
        """Process task and use server's broadcaster for real-time events"""
        
        # If we have server integration, announce it via the server's broadcast endpoint
        if self.shared_broadcaster_available:
            try:
                async with httpx.AsyncClient() as client:
                    # Use the server's broadcast endpoint to send events directly to connected clients
                    await client.post(
                        f"http://localhost:8000/api/agui/broadcast/{task_id}",
                        json={
                            "event_type": "agent_status_changed",
                            "agent_id": self.agent_id,
                            "data": {
                                "old_status": "idle",
                                "new_status": "active",
                                "message": "Agent starting task with server integration"
                            }
                        }
                    )
                    print("📡 Broadcasted status via server endpoint")
            except Exception as e:
                print(f"⚠️  Server broadcast failed, using local broadcaster: {e}")
        
        # Process the task using the original method
        result = await super().process_task(task_id, user_input)
        
        # Broadcast completion via server if available
        if self.shared_broadcaster_available and result.get("success"):
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"http://localhost:8000/api/agui/broadcast/{task_id}",
                        json={
                            "event_type": "agent_completed",
                            "agent_id": self.agent_id,
                            "data": {
                                "success": True,
                                "processing_time": result["metadata"]["processing_time"],
                                "cost": result["metadata"]["cost"],
                                "response_preview": result["response"][:100] + "..."
                            }
                        }
                    )
                    print("📡 Broadcasted completion via server endpoint")
            except Exception as e:
                print(f"⚠️  Server broadcast failed: {e}")
        
        return result


async def test_server_integration():
    """Test demo agent with server broadcaster integration"""
    print("🚀 Testing Demo Agent with Server Integration")
    print("=" * 50)
    
    # Step 1: Check if backend server is running
    print("\n📡 Step 1: Checking backend server connectivity")
    has_connection_manager = await get_shared_broadcaster()
    
    # Step 2: Initialize agent with server integration
    print("\n🤖 Step 2: Initializing agent with server integration")
    agent = ServerIntegratedDemoAgent(
        agent_id="server_integrated_agent", 
        name="Server Integrated Demo Agent"
    )
    
    server_initialized = await agent.initialize_with_server()
    
    # Step 3: Run conversation with real-time broadcasting
    print("\n💬 Step 3: Running conversation with real-time broadcasting")
    task_id = f"server_integration_test_{int(time.time())}"
    
    print(f"Task ID: {task_id}")
    print(f"WebSocket URL: ws://localhost:8000/api/agui/ws/{task_id}")
    print(f"SSE URL: http://localhost:8000/api/agui/stream/{task_id}")
    
    result = await agent.process_task_with_server_integration(
        task_id,
        "Hello! I'm testing the integration between the demo agent and the backend server. Please confirm this is working and tell me about the ATLAS system."
    )
    
    # Step 4: Display results
    print("\n📊 Step 4: Results Summary")
    print("=" * 50)
    
    print(f"✅ Backend Server Connected: {server_initialized}")
    print(f"✅ Shared Broadcaster Available: {agent.shared_broadcaster_available}")
    print(f"✅ Connection Manager Available: {has_connection_manager}")
    print(f"✅ Agent Task Completed: {result.get('success', False)}")
    
    if result.get("success"):
        print(f"📝 Response Preview: {result['response'][:150]}...")
        print(f"💰 Cost: ${result['metadata']['cost']:.6f}")
        print(f"⏱️  Processing Time: {result['metadata']['processing_time']:.2f}s")
        print(f"🎯 Tokens: {result['metadata']['tokens']}")
    
    # Step 5: Verify real-time communication
    print(f"\n🔗 Step 5: Real-time Communication Verification")
    print("To verify real-time updates, connect to:")
    print(f"  • WebSocket: ws://localhost:8000/api/agui/ws/{task_id}")
    print(f"  • SSE Stream: http://localhost:8000/api/agui/stream/{task_id}")
    
    return {
        "server_connected": server_initialized,
        "broadcaster_available": agent.shared_broadcaster_available,
        "connection_manager": has_connection_manager,
        "task_success": result.get("success", False),
        "task_id": task_id
    }


async def main():
    """Main entry point"""
    results = await test_server_integration()
    
    print("\n" + "=" * 50)
    print("🎯 FINAL INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v is True)
    
    for check, status in results.items():
        if isinstance(status, bool):
            emoji = "✅" if status else "❌"
            print(f"{emoji} {check.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
        else:
            print(f"📋 {check.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎉 Integration Score: {passed_checks}/{total_checks-1} checks passed")  # -1 for task_id
    
    if passed_checks >= 3:  # server_connected, broadcaster_available, task_success
        print("🏆 ATLAS AG-UI Integration: SUCCESS!")
        print("🚀 Ready for full multi-agent system development!")
    else:
        print("⚠️  Some integration issues detected. Please review the logs above.")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())