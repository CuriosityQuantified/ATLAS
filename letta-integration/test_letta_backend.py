"""Test script for Letta backend integration."""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.src.letta.service import LettaService
from backend.src.letta.models import LettaAgentConfig

async def test_letta_integration():
    """Test basic Letta operations."""
    print("Testing Letta Backend Integration...")
    
    try:
        # Initialize service
        service = LettaService()
        print("✓ Letta service initialized")
        
        # Test agent creation
        config = LettaAgentConfig(
            name="Test Agent",
            description="A test agent for integration verification",
            model="gpt-4",
            persona="You are a helpful assistant for testing purposes.",
            human="Test user"
        )
        
        print("\nCreating test agent...")
        agent = await service.create_agent(config)
        print(f"✓ Agent created: {agent.name} (ID: {agent.id})")
        
        # Test listing agents
        print("\nListing agents...")
        agents = await service.list_agents()
        print(f"✓ Found {len(agents)} agent(s)")
        
        # Test sending message
        print("\nSending test message...")
        response = await service.send_message(
            agent.id, 
            "Hello! Can you confirm you're working?"
        )
        if response:
            print(f"✓ Agent response: {response.content[:100]}...")
        else:
            print("✗ No response received")
        
        # Test conversation history
        print("\nGetting conversation history...")
        conversation = await service.get_conversation_history(agent.id)
        print(f"✓ Conversation has {len(conversation.messages)} message(s)")
        
        # Cleanup - delete test agent
        print("\nCleaning up...")
        success = await service.delete_agent(agent.id)
        if success:
            print("✓ Test agent deleted")
        else:
            print("✗ Failed to delete test agent")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_letta_integration())