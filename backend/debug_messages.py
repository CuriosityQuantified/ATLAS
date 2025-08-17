#!/usr/bin/env python3
"""Debug script to inspect Letta message structure."""

import os
import sys
sys.path.append('/Users/nicholaspate/Documents/ATLAS/backend')

from src.letta.service import letta_service

def debug_messages():
    """Debug the structure of messages from Letta."""
    agent_id = "agent-d4e261c1-c93c-48ba-bce5-a72025df50de"
    
    print("=== Getting raw messages from Letta ===")
    try:
        # Get raw messages
        messages = letta_service.client.get_in_context_messages(agent_id)
        
        print(f"Total messages: {len(messages)}")
        
        # Look at the last few messages
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        for i, msg in enumerate(recent_messages):
            print(f"\n--- Message {i+1} ---")
            print(f"ID: {getattr(msg, 'id', 'N/A')}")
            print(f"Role: {getattr(msg, 'role', 'N/A')}")
            print(f"Message Type: {type(msg).__name__}")
            
            if hasattr(msg, 'content'):
                content = msg.content
                print(f"Content Type: {type(content)}")
                
                if isinstance(content, list):
                    print(f"Content List Length: {len(content)}")
                    for j, item in enumerate(content):
                        print(f"  Item {j}: {type(item).__name__}")
                        if hasattr(item, 'text'):
                            print(f"    Text: {item.text[:100]}...")
                        elif isinstance(item, dict):
                            print(f"    Dict keys: {list(item.keys())}")
                            if 'text' in item:
                                print(f"    Text: {item['text'][:100]}...")
                elif isinstance(content, str):
                    print(f"Content (string): {content[:200]}...")
                else:
                    print(f"Content: {content}")
            
            if hasattr(msg, 'tool_call_id'):
                print(f"Tool Call ID: {msg.tool_call_id}")
            
            print(f"Class attributes: {[attr for attr in dir(msg) if not attr.startswith('_')]}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_messages()