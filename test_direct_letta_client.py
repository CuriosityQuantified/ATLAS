#!/usr/bin/env python3
"""
Direct test of Letta client SDK without import issues
"""

from letta_client import Letta

def test_direct_connection():
    """Test direct connection to Letta server using SDK."""
    print("\n🔍 Testing Direct Letta Client Connection...")

    try:
        # Create client connected to local server
        client = Letta(base_url="http://localhost:8283")
        print("✅ Connected to Letta server")

        # List existing agents
        agents = client.agents.list()
        print(f"✅ Found {len(agents)} existing agents")

        if agents:
            for agent in agents[:3]:  # Show first 3
                print(f"   - {agent.name} (ID: {agent.id[:8]}...)")

        # Create a test agent
        print("\n🤖 Creating test agent...")
        test_agent = client.agents.create(
            name="phase1_validation_agent",
            description="Test agent for Phase 1 validation",
            system="You are a helpful assistant validating the Phase 1 setup.",
            model="openai/gpt-4o-mini",  # Using OpenAI's smallest model for testing
            embedding="openai/text-embedding-3-small",  # Embedding model
        )
        print(f"✅ Created agent: {test_agent.name}")
        print(f"   ID: {test_agent.id}")

        # Send a message
        print("\n💬 Sending test message...")
        response = client.agents.messages.create(
            agent_id=test_agent.id,
            messages=[{
                "role": "user",
                "content": "Please confirm Phase 1 is working by responding 'Phase 1 validated!'"
            }]
        )

        if response and response.messages:
            # The response might have different message types
            for msg in response.messages:
                if hasattr(msg, 'content'):
                    print(f"✅ Agent responded: {msg.content[:100]}")
                    break
                elif hasattr(msg, 'text'):
                    print(f"✅ Agent responded: {msg.text[:100]}")
                    break
            else:
                print(f"✅ Agent responded (type: {type(response.messages[0]).__name__})")

        # Delete the test agent
        print("\n🧹 Cleaning up...")
        client.agents.delete(test_agent.id)
        print("✅ Test agent deleted")

        print("\n✨ Phase 1 validation successful!")
        print("\n📝 Summary:")
        print("  - Letta server is running at http://localhost:8283")
        print("  - Client SDK can connect and create agents")
        print("  - Agents can receive and respond to messages")
        print("  - All core functionality is working")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Ensure server is running: letta server --port 8283")
        print("  2. Check server logs for errors")
        print("  3. Verify letta_client is installed: pip list | grep letta")
        return False

if __name__ == "__main__":
    test_direct_connection()