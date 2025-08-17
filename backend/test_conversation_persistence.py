#!/usr/bin/env python3
"""Test script for conversation persistence system."""

import os
import sys
import asyncio
sys.path.append('/Users/nicholaspate/Documents/ATLAS/backend')

from src.letta.conversation_persistence import conversation_persistence

async def test_conversation_persistence():
    """Test the conversation persistence system."""
    
    print("=== Testing Conversation Persistence ===")
    
    # Test agent ID (use a real one from our system)
    agent_id = "agent-d4e261c1-c93c-48ba-bce5-a72025df50de"
    
    try:
        # Initialize the persistence layer
        await conversation_persistence.initialize()
        print("✅ Persistence layer initialized")
        
        # Create a session
        session_id = await conversation_persistence.create_session(agent_id)
        print(f"✅ Created session: {session_id}")
        
        # Store a user message (use the session_id)
        user_msg_id = await conversation_persistence.store_message(
            agent_id=agent_id,
            role="user",
            content="Hello, how are you?",
            session_id=session_id,
            tokens_used=4,
            metadata={"source": "test"}
        )
        print(f"✅ Stored user message: {user_msg_id}")
        
        # Store an assistant response (use the same session_id)
        assistant_msg_id = await conversation_persistence.store_message(
            agent_id=agent_id,
            role="assistant",
            content="Hello! I'm doing well, thank you for asking. How can I help you today?",
            session_id=session_id,
            tokens_used=16,
            metadata={"source": "test"}
        )
        print(f"✅ Stored assistant message: {assistant_msg_id}")
        
        # Retrieve conversation history
        messages = await conversation_persistence.get_conversation_history(agent_id)
        print(f"✅ Retrieved {len(messages)} messages from conversation history")
        
        # Display the messages
        for i, msg in enumerate(messages):
            print(f"  Message {i+1}: [{msg.role}] {msg.content[:50]}...")
        
        # Test getting session ID
        retrieved_session_id = await conversation_persistence.get_session_id(agent_id)
        print(f"✅ Retrieved session ID: {retrieved_session_id}")
        
        # End the session
        success = await conversation_persistence.end_session(agent_id)
        print(f"✅ Ended session: {success}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await conversation_persistence.close()
        print("✅ Persistence layer closed")

if __name__ == "__main__":
    asyncio.run(test_conversation_persistence())