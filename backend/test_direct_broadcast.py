#!/usr/bin/env python3
"""Test direct WebSocket broadcast to frontend"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_direct_broadcast():
    """Test broadcasting directly via HTTP endpoint"""
    
    # The task ID from the frontend - try both regular and agent-specific
    task_ids = [
        "task_1751754205_327e363d",  # Regular task ID
        "global_supervisor_task_1751754205_327e363d"  # Agent-specific ID
    ]
    
    # Test broadcasting a tool call event
    events = [
        {
            "event_type": "tool_call_initiated",
            "agent_id": "global_supervisor",
            "data": {
                "tool_call_id": "direct_test_001",
                "tool_name": "analyze_request",
                "arguments": {"query": "Analyzing your request..."},
                "initiated_at": datetime.now().isoformat()
            }
        },
        {
            "event_type": "tool_call_executing",
            "agent_id": "global_supervisor",
            "data": {
                "tool_call_id": "direct_test_001",
                "tool_name": "analyze_request",
                "executing_at": datetime.now().isoformat()
            }
        },
        {
            "event_type": "tool_call_completed",
            "agent_id": "global_supervisor",
            "data": {
                "tool_call_id": "direct_test_001",
                "tool_name": "analyze_request",
                "result": {"analysis": "Request analyzed successfully", "type": "greeting"},
                "execution_time_ms": 1500,
                "completed_at": datetime.now().isoformat()
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for task_id in task_ids:
            print(f"\nTesting with task_id: {task_id}")
            
            for i, event in enumerate(events):
                print(f"  Sending event {i+1}/{len(events)}: {event['event_type']}")
                
                # Use the broadcast endpoint
                url = f"http://localhost:8000/api/agui/broadcast/{task_id}"
                
                async with session.post(url, json=event) as resp:
                    result = await resp.json()
                    print(f"  Response: {result}")
                
                # Wait between events
                if i < len(events) - 1:
                    await asyncio.sleep(0.5)
    
    print("\nTest complete! Check frontend for tool call display.")

if __name__ == "__main__":
    asyncio.run(test_direct_broadcast())