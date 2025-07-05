#!/usr/bin/env python3
"""Test streaming functionality with thinking display"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_streaming_demo():
    """Demonstrate streaming with thinking updates"""
    
    # The task ID from the frontend
    task_id = "task_1751754205_327e363d"
    
    # Simulate a complete streaming sequence
    events = [
        # Start typing
        {
            "event_type": "agent_status_changed",
            "agent_id": "global_supervisor",
            "data": {
                "old_status": "idle",
                "new_status": "typing",
                "changed_at": datetime.now().isoformat()
            }
        },
        # Start thinking
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_thinking_update",
                "thinking_status": "started",
                "thinking_content": "",
                "timestamp": datetime.now().isoformat()
            }
        },
        # Thinking chunks
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_thinking_update",
                "thinking_status": "chunk",
                "thinking_content": "The user sent a greeting 'hi'. ",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_thinking_update",
                "thinking_status": "chunk",
                "thinking_content": "I should acknowledge this and analyze their intent. ",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_thinking_update",
                "thinking_status": "chunk",
                "thinking_content": "Let me use the analyze_request tool.",
                "timestamp": datetime.now().isoformat()
            }
        },
        # Complete thinking
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_thinking_update",
                "thinking_status": "complete",
                "thinking_content": "The user sent a greeting 'hi'. I should acknowledge this and analyze their intent. Let me use the analyze_request tool.",
                "timestamp": datetime.now().isoformat()
            }
        },
        # Start content streaming
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_content_stream",
                "stream_status": "started",
                "content": "",
                "timestamp": datetime.now().isoformat()
            }
        },
        # Content chunks
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_content_stream",
                "stream_status": "chunk",
                "content": "I'll analyze ",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_content_stream",
                "stream_status": "chunk",
                "content": "your request ",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_content_stream",
                "stream_status": "chunk",
                "content": "and see how ",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_content_stream",
                "stream_status": "chunk",
                "content": "I can help.\n\n",
                "timestamp": datetime.now().isoformat()
            }
        },
        # Complete streaming
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "agent_content_stream",
                "stream_status": "complete",
                "full_content": "I'll analyze your request and see how I can help.\n\n",
                "timestamp": datetime.now().isoformat()
            }
        },
        # Tool call stream
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "tool_call_stream_update",
                "tool_call_id": "stream_001",
                "tool_name": "analyze_request",
                "status": "started",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "event_type": "system_message",
            "agent_id": "global_supervisor",
            "data": {
                "event_type": "tool_call_stream_update",
                "tool_call_id": "stream_001",
                "tool_name": "analyze_request",
                "status": "ready",
                "arguments": {"query": "Analyzing your greeting..."},
                "timestamp": datetime.now().isoformat()
            }
        },
        # Regular tool call events
        {
            "event_type": "tool_call_initiated",
            "agent_id": "global_supervisor",
            "data": {
                "tool_call_id": "stream_001",
                "tool_name": "analyze_request",
                "arguments": {"query": "Analyzing your greeting..."},
                "initiated_at": datetime.now().isoformat()
            }
        },
        # Stop typing
        {
            "event_type": "agent_status_changed",
            "agent_id": "global_supervisor",
            "data": {
                "old_status": "typing",
                "new_status": "idle",
                "changed_at": datetime.now().isoformat()
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        print(f"Testing streaming demo with task_id: {task_id}")
        
        for i, event in enumerate(events):
            print(f"  Sending event {i+1}/{len(events)}: {event.get('data', {}).get('event_type', event['event_type'])}")
            
            # Use the broadcast endpoint
            url = f"http://localhost:8000/api/agui/broadcast/{task_id}"
            
            async with session.post(url, json=event) as resp:
                result = await resp.json()
                print(f"  Response: {result}")
            
            # Simulate realistic timing
            if "thinking" in str(event):
                await asyncio.sleep(0.3)  # Thinking is fast
            elif "chunk" in str(event):
                await asyncio.sleep(0.1)  # Streaming is smooth
            else:
                await asyncio.sleep(0.5)  # Other events
    
    print("\nStreaming demo complete! Check frontend for display.")

if __name__ == "__main__":
    asyncio.run(test_streaming_demo())