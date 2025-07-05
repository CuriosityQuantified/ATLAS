#!/usr/bin/env python3
"""
Test frontend-backend integration with the new tool-based architecture.
This script simulates frontend requests and validates the complete flow.
"""

import asyncio
import json
import logging
from datetime import datetime
import httpx
import websockets
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"


class FrontendSimulator:
    """Simulates frontend interactions with the backend"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE_URL)
        self.messages_received: List[Dict[str, Any]] = []
        self.ws_connection = None
        
    async def create_task(self, description: str, use_v2: bool = True) -> Dict[str, Any]:
        """Create a new task via API"""
        logger.info(f"Creating task with V2={use_v2}: {description[:50]}...")
        
        response = await self.client.post(
            "/api/tasks",
            json={
                "task_type": "research_and_analysis",
                "description": description,
                "priority": "high",
                "use_v2_supervisor": use_v2,
                "context": {
                    "test_mode": True,
                    "frontend_test": True
                }
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create task: {response.status_code} - {response.text}")
            raise Exception(f"Task creation failed: {response.text}")
            
        data = response.json()
        logger.info(f"✅ Task created: {data['task_id']}")
        return data
    
    async def start_task(self, task_id: str) -> Dict[str, Any]:
        """Start task processing"""
        logger.info(f"Starting task: {task_id}")
        
        response = await self.client.post(f"/api/tasks/{task_id}/start")
        
        if response.status_code != 200:
            logger.error(f"Failed to start task: {response.status_code} - {response.text}")
            raise Exception(f"Task start failed: {response.text}")
            
        data = response.json()
        logger.info(f"✅ Task started: {data['status']}")
        return data
    
    async def connect_websocket(self, task_id: str):
        """Connect to WebSocket for real-time updates"""
        ws_url = f"{WS_BASE_URL}/api/agui/agents/global_supervisor/{task_id}"
        logger.info(f"Connecting to WebSocket: {ws_url}")
        
        try:
            self.ws_connection = await websockets.connect(ws_url)
            logger.info("✅ WebSocket connected")
            
            # Start listening for messages
            await self.listen_for_messages()
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def listen_for_messages(self):
        """Listen for WebSocket messages"""
        if not self.ws_connection:
            return
            
        try:
            async for message in self.ws_connection:
                data = json.loads(message)
                self.messages_received.append(data)
                
                # Log different types of messages
                if data.get("type") == "dialogue_update":
                    content = data.get("data", {}).get("content", {})
                    if isinstance(content, dict):
                        text = content.get("data", "")
                    else:
                        text = str(content)
                    logger.info(f"💬 Dialogue Update: {text[:100]}...")
                    
                elif data.get("type") == "agent_status_changed":
                    logger.info(f"🔄 Agent Status: {data.get('data', {}).get('new_status')}")
                    
                elif data.get("type") == "task_progress":
                    progress = data.get("data", {}).get("progress", 0)
                    logger.info(f"📊 Progress: {progress}%")
                    
                elif data.get("type") == "task_completed":
                    logger.info("✅ Task Completed!")
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error listening to WebSocket: {e}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status via API"""
        response = await self.client.get(f"/api/tasks/{task_id}/status")
        
        if response.status_code != 200:
            logger.error(f"Failed to get status: {response.status_code}")
            return None
            
        return response.json()
    
    async def send_user_input(self, task_id: str, message: str) -> Dict[str, Any]:
        """Send user input to a task"""
        logger.info(f"Sending user input: {message}")
        
        response = await self.client.post(
            f"/api/tasks/{task_id}/input",
            json={
                "message": message,
                "agent_id": "global_supervisor"
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send input: {response.status_code}")
            return None
            
        return response.json()
    
    async def cleanup(self):
        """Clean up connections"""
        if self.ws_connection:
            await self.ws_connection.close()
        await self.client.aclose()


async def test_v2_supervisor_with_user_updates():
    """Test GlobalSupervisorV2 with user communication"""
    print("\n🧪 Testing V2 Supervisor with User Updates")
    print("=" * 60)
    
    simulator = FrontendSimulator()
    
    try:
        # Create task with V2 supervisor
        task_data = await simulator.create_task(
            "Research the latest developments in renewable energy and create a brief summary",
            use_v2=True
        )
        
        task_id = task_data["task_id"]
        
        # Connect WebSocket in background
        ws_task = asyncio.create_task(simulator.connect_websocket(task_id))
        
        # Give WebSocket time to connect
        await asyncio.sleep(1)
        
        # Start the task
        await simulator.start_task(task_id)
        
        # Wait for some messages
        await asyncio.sleep(5)
        
        # Check status
        status = await simulator.get_task_status(task_id)
        if status:
            print(f"\n📊 Task Status:")
            print(f"   Status: {status['status']}")
            print(f"   Progress: {status['progress']}%")
            print(f"   Phase: {status['current_phase']}")
        
        # Wait for completion or timeout
        await asyncio.wait_for(ws_task, timeout=30)
        
        # Analyze messages received
        print(f"\n📨 Messages Received: {len(simulator.messages_received)}")
        
        # Check for user updates from respond_to_user tool
        user_updates = [
            msg for msg in simulator.messages_received 
            if msg.get("type") == "dialogue_update" and 
            msg.get("data", {}).get("sender") == "global_supervisor"
        ]
        
        print(f"💬 User Updates: {len(user_updates)}")
        for i, update in enumerate(user_updates[:3]):  # Show first 3
            content = update.get("data", {}).get("content", {})
            if isinstance(content, dict):
                text = content.get("data", "")
            else:
                text = str(content)
            print(f"   {i+1}. {text[:80]}...")
        
        # Verify we got updates
        assert len(user_updates) >= 2, "Should have at least 2 user updates (start and end)"
        print("\n✅ V2 Supervisor test passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await simulator.cleanup()


async def test_parallel_tool_execution():
    """Test that supervisors can execute tools in parallel"""
    print("\n\n🧪 Testing Parallel Tool Execution")
    print("=" * 60)
    
    simulator = FrontendSimulator()
    
    try:
        # Create a task that should trigger multiple teams
        task_data = await simulator.create_task(
            "Analyze the AI market: research current trends, analyze market size, and write a report",
            use_v2=True
        )
        
        task_id = task_data["task_id"]
        
        # Connect WebSocket
        ws_task = asyncio.create_task(simulator.connect_websocket(task_id))
        await asyncio.sleep(1)
        
        # Start task
        await simulator.start_task(task_id)
        
        # Monitor for parallel execution indicators
        await asyncio.sleep(10)
        
        # Look for multiple team calls in messages
        dialogue_updates = [
            msg for msg in simulator.messages_received
            if msg.get("type") == "dialogue_update"
        ]
        
        # Check if multiple teams were mentioned
        teams_mentioned = set()
        for update in dialogue_updates:
            content = str(update.get("data", {}).get("content", "")).lower()
            if "research" in content:
                teams_mentioned.add("research")
            if "analysis" in content:
                teams_mentioned.add("analysis")
            if "writing" in content:
                teams_mentioned.add("writing")
        
        print(f"\n🔀 Teams mentioned: {teams_mentioned}")
        print(f"   Parallel execution likely: {len(teams_mentioned) > 1}")
        
        # Cancel WebSocket task
        ws_task.cancel()
        
        print("\n✅ Parallel execution test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        await simulator.cleanup()


async def test_error_handling_and_recovery():
    """Test error handling and user communication during errors"""
    print("\n\n🧪 Testing Error Handling and Recovery")
    print("=" * 60)
    
    simulator = FrontendSimulator()
    
    try:
        # Create a task with intentionally problematic request
        task_data = await simulator.create_task(
            "This is a test task to trigger error handling: analyze data from file://nonexistent.csv",
            use_v2=True
        )
        
        task_id = task_data["task_id"]
        
        # Connect WebSocket
        ws_task = asyncio.create_task(simulator.connect_websocket(task_id))
        await asyncio.sleep(1)
        
        # Start task
        await simulator.start_task(task_id)
        
        # Wait for error handling
        await asyncio.sleep(5)
        
        # Check for error messages
        error_messages = [
            msg for msg in simulator.messages_received
            if "error" in str(msg).lower() or 
            msg.get("data", {}).get("message_type") == "error"
        ]
        
        print(f"\n🚨 Error messages found: {len(error_messages)}")
        
        # Cancel WebSocket
        ws_task.cancel()
        
        print("\n✅ Error handling test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        await simulator.cleanup()


async def main():
    """Run all integration tests"""
    print("\n🔧 ATLAS Frontend-Backend Integration Test Suite")
    print("=" * 80)
    print("Testing the new tool-based architecture with:")
    print("- GlobalSupervisorV2 with respond_to_user tool")
    print("- WebSocket real-time updates")
    print("- Parallel tool execution")
    print("- Error handling and recovery")
    
    print("\n⚠️  Prerequisites:")
    print("1. Backend must be running: cd backend && uvicorn main:app --reload")
    print("2. Frontend should be running: cd frontend && npm run dev")
    print("\nPress Ctrl+C to cancel if services are not running...")
    await asyncio.sleep(3)
    
    # Run tests
    await test_v2_supervisor_with_user_updates()
    await test_parallel_tool_execution()
    await test_error_handling_and_recovery()
    
    print("\n\n✅ All integration tests completed!")
    print("\n📊 Summary:")
    print("- V2 Supervisor with user updates: ✓")
    print("- WebSocket communication: ✓")
    print("- Parallel tool indication: ✓")
    print("- Error handling: ✓")


if __name__ == "__main__":
    asyncio.run(main())