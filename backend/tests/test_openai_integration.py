#!/usr/bin/env python3
"""
Test OpenAI integration with Letta agents.
Verifies that agents can be created and messages can be sent using OpenAI models.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from src.agents.agent_factory import LettaAgentFactory
from src.config.openai_config import OpenAIConfig
from letta import LLMConfig, EmbeddingConfig
from letta_client import MessageCreate
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


def test_openai_config():
    """Test OpenAI configuration module."""
    print("\n=== Testing OpenAI Configuration ===\n")

    # Test model retrieval
    supervisor_model = OpenAIConfig.get_model_for_agent("supervisor")
    research_model = OpenAIConfig.get_model_for_agent("research")

    print(f"✓ Supervisor model: {supervisor_model}")
    print(f"✓ Research model: {research_model}")

    # Test LLM config generation
    llm_config = OpenAIConfig.get_llm_config(agent_type="supervisor")
    print(f"\n✓ LLM Config generated:")
    print(f"  - Model: {llm_config['model']}")
    print(f"  - Endpoint: {llm_config['model_endpoint']}")
    print(f"  - Context window: {llm_config['context_window']}")

    # Test embedding config
    embedding_config = OpenAIConfig.get_embedding_config()
    print(f"\n✓ Embedding Config generated:")
    print(f"  - Model: {embedding_config['embedding_model']}")
    print(f"  - Dimensions: {embedding_config['embedding_dim']}")

    return True


def test_agent_creation():
    """Test creating agents with OpenAI models."""
    print("\n=== Testing Agent Creation with OpenAI ===\n")

    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("✗ OPENAI_API_KEY not found in environment")
        return False
    else:
        print(f"✓ OPENAI_API_KEY found: {api_key[:10]}...")

    try:
        # Initialize agent factory
        factory = LettaAgentFactory()
        print("✓ Agent factory initialized")

        # Create a test supervisor agent
        task_id = f"test_{datetime.now().strftime('%H%M%S')}"

        print("\n Creating supervisor agent...")
        supervisor = factory.create_supervisor_agent(task_id)

        print(f"✓ Supervisor agent created:")
        print(f"  - Name: {supervisor.name}")
        print(f"  - ID: {supervisor.id}")

        # Test sending a message
        print("\n Sending test message...")
        response = factory.client.agents.messages.create(
            agent_id=supervisor.id,
            messages=[
                MessageCreate(
                    role="user",
                    content="Hello! Please confirm you're using OpenAI GPT-4o model."
                )
            ]
        )

        print(f"✓ Response received from supervisor")

        # Check response content
        if response and response.messages:
            for msg in response.messages:
                if hasattr(msg, 'text') and msg.text:
                    print(f"  Agent response: {msg.text[:200]}...")
                    break
                elif hasattr(msg, 'content') and msg.content:
                    print(f"  Agent response: {msg.content[:200]}...")
                    break

        # Create a research agent
        print("\n Creating research agent...")
        research = factory.create_research_agent(task_id, "Test research context")

        print(f"✓ Research agent created:")
        print(f"  - Name: {research.name}")
        print(f"  - ID: {research.id}")

        # Test research agent
        response = factory.client.agents.messages.create(
            agent_id=research.id,
            messages=[
                MessageCreate(
                    role="user",
                    content="What model are you using? Please confirm you're using GPT-4o-mini."
                )
            ]
        )

        print(f"✓ Response received from research agent")

        # Clean up
        print("\n Cleaning up...")
        factory.delete_agent(supervisor.id)
        factory.delete_agent(research.id)
        print("✓ Test agents deleted")

        return True

    except Exception as e:
        print(f"✗ Error creating agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_agent_types():
    """Test creating all agent types with OpenAI."""
    print("\n=== Testing All Agent Types ===\n")

    try:
        factory = LettaAgentFactory()
        task_id = f"test_{datetime.now().strftime('%H%M%S')}"
        agents_created = []

        # Test supervisor (GPT-4o)
        print("Creating supervisor agent (GPT-4o)...")
        supervisor = factory.create_supervisor_agent(task_id)
        agents_created.append(supervisor.id)
        print(f"✓ Supervisor: {supervisor.name}")

        # Test research (GPT-4o-mini)
        print("Creating research agent (GPT-4o-mini)...")
        research = factory.create_research_agent(task_id, "Test context")
        agents_created.append(research.id)
        print(f"✓ Research: {research.name}")

        # Test analysis (GPT-4o-mini)
        print("Creating analysis agent (GPT-4o-mini)...")
        analysis = factory.create_analysis_agent(task_id, "Test context")
        agents_created.append(analysis.id)
        print(f"✓ Analysis: {analysis.name}")

        # Test writing (GPT-4o)
        print("Creating writing agent (GPT-4o)...")
        writing = factory.create_writing_agent(task_id, "Test context")
        agents_created.append(writing.id)
        print(f"✓ Writing: {writing.name}")

        # Clean up
        print("\nCleaning up all test agents...")
        for agent_id in agents_created:
            factory.delete_agent(agent_id)
        print(f"✓ Deleted {len(agents_created)} test agents")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

        # Clean up any created agents
        if 'agents_created' in locals():
            for agent_id in agents_created:
                try:
                    factory.delete_agent(agent_id)
                except:
                    pass

        return False


def main():
    """Run all OpenAI integration tests."""
    print("\n" + "="*50)
    print("  ATLAS OpenAI Integration Tests")
    print("="*50)

    # Track results
    results = []

    # Test 1: Configuration
    results.append(("OpenAI Configuration", test_openai_config()))

    # Test 2: Agent creation and messaging
    results.append(("Agent Creation & Messaging", test_agent_creation()))

    # Test 3: All agent types
    results.append(("All Agent Types", test_all_agent_types()))

    # Summary
    print("\n" + "="*50)
    print("  Test Summary")
    print("="*50 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:30} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! OpenAI integration is working.")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")

    return passed == total


if __name__ == "__main__":
    # Run the tests
    success = main()
    sys.exit(0 if success else 1)