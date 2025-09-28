#!/usr/bin/env python3
"""
Test script to verify Letta server connection and create a test agent
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

def test_letta_connection():
    """Test connection to local Letta server and create an agent."""
    print("\n🔍 Testing Letta Server Connection...")

    try:
        # Import our agent factory
        from agents.agent_factory import LettaAgentFactory

        # Create factory instance (will connect to local server)
        print("📡 Connecting to Letta server at http://localhost:8283...")
        factory = LettaAgentFactory()

        print("✅ Successfully connected to Letta server!")

        # List existing agents
        print("\n📋 Existing agents:")
        agents = factory.list_agents()
        if agents:
            for agent in agents:
                print(f"  - {agent.name} (ID: {agent.id})")
        else:
            print("  No agents found")

        # Create a test agent
        print("\n🤖 Creating test agent...")
        test_agent = factory.create_supervisor_agent("test_task_001")
        print(f"✅ Created agent: {test_agent.name}")
        print(f"   ID: {test_agent.id}")

        # Send a test message
        print("\n💬 Sending test message...")
        response = factory.send_message_to_agent(
            test_agent.id,
            "Hello! Can you confirm you're working?"
        )
        print(f"✅ Agent responded: {response[0] if response else 'No response'}")

        # Get ADE debug info
        debug_info = factory.get_ade_debug_info(test_agent.id)
        print("\n🌐 Web ADE Debug Info:")
        for instruction in debug_info.get("instructions", []):
            print(f"  {instruction}")

        print("\n✨ All tests passed! Letta server is working correctly.")
        print("\n📝 Note: If Web ADE won't connect, try:")
        print("  1. Using http://127.0.0.1:8283 instead of localhost")
        print("  2. Allowing insecure content in browser settings")
        print("  3. Using the built-in UI at http://localhost:8283")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Ensure Letta server is running: ./scripts/dev/start-letta-with-ade.sh")
        print("  2. Check server is accessible: curl http://localhost:8283")
        print("  3. Verify no firewall blocking port 8283")
        return False

if __name__ == "__main__":
    test_letta_connection()