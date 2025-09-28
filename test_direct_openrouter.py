#!/usr/bin/env python3
"""
Direct test of OpenRouter with Letta using the correct configuration
"""

import os
from letta_client import Letta, LLMConfig, EmbeddingConfig
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openrouter_direct():
    """Test OpenRouter integration directly with Letta client."""
    print("🔍 Testing Direct OpenRouter Integration...")

    try:
        # Create client connected to local server
        client = Letta(base_url="http://localhost:8283")
        print("✅ Connected to Letta server")

        # Get API keys
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if not openrouter_key:
            print("❌ OPENROUTER_API_KEY not found")
            return False

        if not openai_key:
            print("❌ OPENAI_API_KEY not found")
            return False

        print(f"✅ OpenRouter key: {openrouter_key[:10]}...")
        print(f"✅ OpenAI key: {openai_key[:10]}...")

        # Test different LLM config approaches
        configs_to_test = [
            {
                "name": "With model_api_key",
                "config": {
                    "model": "openrouter/moonshotai/kimi-k2-0905",
                    "model_endpoint_type": "openai",
                    "model_endpoint": "https://openrouter.ai/api/v1",
                    "context_window": 200000,
                    "model_api_key": openrouter_key
                }
            },
            {
                "name": "Simple with prefix",
                "config": {
                    "model": "openrouter/moonshotai/kimi-k2-0905",
                    "model_api_key": openrouter_key
                }
            },
            {
                "name": "Without prefix",
                "config": {
                    "model": "moonshotai/kimi-k2-0905",
                    "model_endpoint_type": "openai",
                    "model_endpoint": "https://openrouter.ai/api/v1",
                    "model_api_key": openrouter_key
                }
            }
        ]

        # Create embedding config
        embedding_config = EmbeddingConfig(
            embedding_model="text-embedding-3-small",
            embedding_endpoint_type="openai",
            embedding_endpoint="https://api.openai.com/v1",
            embedding_dim=1536,
            embedding_chunk_size=300,
            embedding_api_key=openai_key
        )

        for test_config in configs_to_test:
            print(f"\n🧪 Testing: {test_config['name']}")

            try:
                # Create LLM config
                llm_config = LLMConfig(**test_config['config'])

                # Create test agent
                agent = client.agents.create(
                    name=f"test_openrouter_{test_config['name'].lower().replace(' ', '_')}",
                    description=f"Test agent with {test_config['name']}",
                    system="You are a test agent using OpenRouter.",
                    llm_config=llm_config,
                    embedding_config=embedding_config
                )

                print(f"✅ Agent created: {agent.name}")
                print(f"   ID: {agent.id}")

                # Test sending a message
                response = client.agents.messages.create(
                    agent_id=agent.id,
                    messages=[{
                        "role": "user",
                        "content": "Say 'Configuration working' in exactly 3 words"
                    }]
                )

                if response and response.messages:
                    print(f"✅ Agent responded successfully")
                    for msg in response.messages:
                        if hasattr(msg, 'content') and msg.content:
                            print(f"   Response: {msg.content[:100]}")
                            break
                        elif hasattr(msg, 'text') and msg.text:
                            print(f"   Response: {msg.text[:100]}")
                            break

                # Clean up
                client.agents.delete(agent.id)
                print(f"✅ Test agent deleted")

                # If we get here, this configuration works!
                print(f"🎉 SUCCESS: {test_config['name']} configuration works!")
                return True

            except Exception as e:
                print(f"❌ Failed with {test_config['name']}: {e}")
                continue

        print("❌ All configurations failed")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_openrouter_direct()
    if success:
        print("\n✨ OpenRouter integration working!")
    else:
        print("\n⚠️ OpenRouter integration needs fixes")