#!/usr/bin/env python3
"""
Test OpenRouter integration with ATLAS agents.
Tests model configuration, fallback hierarchy, and embedding setup.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

# Load environment variables
load_dotenv(project_root / ".env")

from src.config.openrouter_config import OpenRouterConfig
from src.agents.agent_factory import LettaAgentFactory
from src.utils.call_model import CallModel
from letta import LLMConfig, EmbeddingConfig
from letta_client import MessageCreate


async def test_openrouter_models():
    """Test OpenRouter model configuration and fallback."""
    print("\n=== Testing OpenRouter Model Configuration ===\n")

    # Test configuration retrieval
    config = OpenRouterConfig()

    # Test primary model
    primary_model = config.get_primary_model()
    print(f"✓ Primary model: {primary_model}")

    # Test model fallback list
    fallback_list = config.get_fallback_list()
    print(f"✓ Fallback models configured: {len(fallback_list)} models")
    for model in fallback_list[:3]:  # Show first 3
        print(f"  - Priority {model['priority']}: {model['model']} via {model['provider']}")

    # Test LLM config generation
    llm_config = config.get_llm_config(model_priority=0)
    print(f"\n✓ LLM Config generated:")
    print(f"  - Model: {llm_config['model']}")
    print(f"  - Endpoint: {llm_config['model_endpoint']}")
    print(f"  - Context window: {llm_config['context_window']}")
    print(f"  - Provider preference: {llm_config['extra_headers'].get('X-Provider-Order')}")

    return True


async def test_call_model_with_openrouter():
    """Test CallModel with OpenRouter models."""
    print("\n=== Testing CallModel with OpenRouter ===\n")

    # Initialize CallModel
    call_model = CallModel()

    # Test model name
    model_name = "openrouter/moonshotai/kimi-k2-0905"

    print(f"Testing model: {model_name}")
    print("Sending test message...")

    try:
        # Test the call using the correct signature
        response = await call_model.call_model(
            model_name=model_name,
            most_recent_message="Say 'OpenRouter test successful' in exactly 5 words",
            temperature=0.1,
            max_tokens=50
        )

        if response.success:
            print(f"✓ Response received: {response.content}")
            print(f"✓ Provider: {response.provider}")
            print(f"✓ Model used: {response.model_name}")
            print(f"✓ Tokens: {response.total_tokens}")
            return True
        else:
            print(f"✗ Call failed: {response.error}")
            return False

    except Exception as e:
        print(f"✗ Error calling model: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_creation_with_openrouter():
    """Test creating a Letta agent with OpenRouter configuration."""
    print("\n=== Testing Agent Creation with OpenRouter ===\n")

    # Check environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("✗ OPENROUTER_API_KEY not found in environment")
        return False
    else:
        print(f"✓ OPENROUTER_API_KEY found: {api_key[:10]}...")

    if not openai_key:
        print("✗ OPENAI_API_KEY not found (needed for embeddings)")
        return False
    else:
        print(f"✓ OPENAI_API_KEY found: {openai_key[:10]}...")

    try:
        # Initialize the agent factory
        factory = LettaAgentFactory()

        # Get OpenRouter config with API key
        or_config = OpenRouterConfig.get_llm_config(model_priority=0, api_key=api_key)

        # Create explicit LLM config with API key
        llm_config = LLMConfig(
            model=or_config["model"],
            model_endpoint_type=or_config["model_endpoint_type"],
            model_endpoint=or_config["model_endpoint"],
            context_window=or_config["context_window"],
            model_wrapper=None,
            model_api_key=or_config.get("model_api_key")  # Use API key from config
        )

        print(f"\nLLM Configuration:")
        print(f"  - Model: {llm_config.model}")
        print(f"  - Endpoint type: {llm_config.model_endpoint_type}")
        print(f"  - Endpoint: {llm_config.model_endpoint}")
        print(f"  - Context window: {llm_config.context_window}")

        # Create explicit embedding config for OpenAI
        embedding_config = EmbeddingConfig(
            embedding_model="text-embedding-3-small",
            embedding_endpoint_type="openai",
            embedding_endpoint="https://api.openai.com/v1",
            embedding_dim=1536,
            embedding_chunk_size=300,
            embedding_api_key=os.getenv("OPENAI_API_KEY")  # Add the API key
        )

        print(f"\nEmbedding Configuration:")
        print(f"  - Model: {embedding_config.embedding_model}")
        print(f"  - Endpoint type: {embedding_config.embedding_endpoint_type}")
        print(f"  - Endpoint: {embedding_config.embedding_endpoint}")
        print(f"  - Dimensions: {embedding_config.embedding_dim}")

        # Create a test agent
        print("\n Creating supervisor agent...")

        # Use the client directly to create agent with both configs
        agent = factory.client.agents.create(
            name="test_openrouter_agent",
            description="Test agent with OpenRouter and OpenAI embeddings",
            system="You are a test agent using OpenRouter models and OpenAI embeddings.",
            llm_config=llm_config,
            embedding_config=embedding_config
        )

        print(f"✓ Agent created: {agent.name}")
        print(f"✓ Agent ID: {agent.id}")

        # Test sending a message
        print("\nSending test message to agent...")
        response = factory.client.agents.messages.create(
            agent_id=agent.id,
            messages=[
                MessageCreate(
                    role="user",
                    content="Hello! Please confirm you're using OpenRouter models."
                )
            ]
        )

        print(f"✓ Response received from agent")
        for msg in response.messages:
            if hasattr(msg, 'text') and msg.text:
                print(f"  Agent: {msg.text[:200]}...")
                break

        # Clean up - delete the test agent
        print("\nCleaning up...")
        factory.client.agents.delete(agent.id)
        print(f"✓ Test agent deleted")

        return True

    except Exception as e:
        print(f"✗ Error creating agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all OpenRouter integration tests."""
    print("\n" + "="*50)
    print("  ATLAS OpenRouter Integration Tests")
    print("="*50)

    # Track results
    results = []

    # Test 1: Configuration
    results.append(("OpenRouter Configuration", await test_openrouter_models()))

    # Test 2: CallModel integration
    results.append(("CallModel Integration", await test_call_model_with_openrouter()))

    # Test 3: Agent creation
    results.append(("Agent Creation", await test_agent_creation_with_openrouter()))

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
        print("\n🎉 All tests passed! OpenRouter integration is working.")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")

    return passed == total


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)