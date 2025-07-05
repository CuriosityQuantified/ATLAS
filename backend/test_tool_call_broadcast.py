#!/usr/bin/env python3
"""Test tool call broadcasting to frontend"""

import asyncio
import json
from datetime import datetime
from src.agui.handlers import AGUIEventBroadcaster
from src.agui.server import AGUIConnectionManager

async def test_tool_call_broadcast():
    """Test broadcasting tool call events"""
    
    # Create connection manager and broadcaster
    connection_manager = AGUIConnectionManager()
    broadcaster = AGUIEventBroadcaster(connection_manager=connection_manager)
    
    # Task ID that matches the frontend connection
    task_id = "global_supervisor_task_1751754205_327e363d"
    agent_id = "global_supervisor"
    tool_call_id = "test_call_001"
    
    print(f"Testing tool call broadcast to task: {task_id}")
    
    # Broadcast tool call initiated
    print("Broadcasting tool_call_initiated...")
    await broadcaster.broadcast_tool_call_initiated(
        task_id=task_id,
        agent_id=agent_id,
        tool_call_id=tool_call_id,
        tool_name="test_analysis_tool",
        arguments={"query": "test query", "depth": 3}
    )
    
    # Wait a bit
    await asyncio.sleep(1)
    
    # Broadcast tool call executing
    print("Broadcasting tool_call_executing...")
    await broadcaster.broadcast_tool_call_executing(
        task_id=task_id,
        agent_id=agent_id,
        tool_call_id=tool_call_id,
        tool_name="test_analysis_tool"
    )
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Broadcast tool call completed
    print("Broadcasting tool_call_completed...")
    await broadcaster.broadcast_tool_call_completed(
        task_id=task_id,
        agent_id=agent_id,
        tool_call_id=tool_call_id,
        tool_name="test_analysis_tool",
        result={"analysis": "Test analysis complete", "confidence": 0.95},
        execution_time_ms=2500
    )
    
    print("Test complete! Check frontend for tool call display.")

if __name__ == "__main__":
    asyncio.run(test_tool_call_broadcast())