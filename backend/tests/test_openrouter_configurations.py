#!/usr/bin/env python3
"""
Comprehensive OpenRouter Configuration Testing Suite
Tests multiple API key configurations and endpoint setups to identify
the correct pattern for Letta-OpenRouter integration.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from letta_client import Letta
from letta import LLMConfig, EmbeddingConfig
from src.config.openrouter_config import OpenRouterConfig

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


@dataclass
class TestResult:
    """Result of a single configuration test."""
    config_name: str
    success: bool
    agent_created: bool = False
    message_sent: bool = False
    response_received: bool = False
    error: Optional[str] = None
    error_type: Optional[str] = None
    response_content: Optional[str] = None
    model_used: Optional[str] = None
    provider_detected: Optional[str] = None


class OpenRouterConfigTester:
    """Comprehensive tester for OpenRouter configurations."""

    def __init__(self):
        self.client = None
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.results: List[TestResult] = []

    def setup(self) -> bool:
        """Setup test environment and verify prerequisites."""
        print("\n" + "="*60)
        print("  OpenRouter Configuration Testing Suite")
        print("="*60 + "\n")

        # Check API keys
        if not self.openrouter_key:
            print("❌ OPENROUTER_API_KEY not found in environment")
            return False
        print(f"✅ OpenRouter API Key: {self.openrouter_key[:10]}...")

        if not self.openai_key:
            print("❌ OPENAI_API_KEY not found for embeddings")
            return False
        print(f"✅ OpenAI API Key: {self.openai_key[:10]}...")

        # Connect to Letta server
        try:
            self.client = Letta(base_url="http://localhost:8283")
            print("✅ Connected to Letta server")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Letta server: {e}")
            return False

    def get_embedding_config(self) -> EmbeddingConfig:
        """Get standard embedding configuration."""
        return EmbeddingConfig(
            embedding_model="text-embedding-3-small",
            embedding_endpoint_type="openai",
            embedding_endpoint="https://api.openai.com/v1",
            embedding_dim=1536,
            embedding_chunk_size=300,
            embedding_api_key=self.openai_key
        )

    def get_test_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Get all LLM configurations to test."""
        configs = {}

        # Test 1: Standard OpenRouter Configuration (from docs)
        configs["standard_openrouter"] = {
            "model": "moonshotai/kimi-k2-0905",  # No prefix
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "model_api_key": self.openrouter_key,
            "context_window": 200000
        }

        # Test 2: With OpenRouter Prefix
        configs["with_prefix"] = {
            "model": "openrouter/moonshotai/kimi-k2-0905",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "model_api_key": self.openrouter_key,
            "context_window": 200000
        }

        # Test 3: Minimal Configuration
        configs["minimal_with_prefix"] = {
            "model": "openrouter/moonshotai/kimi-k2-0905",
            "model_api_key": self.openrouter_key
        }

        # Test 4: Custom Headers Approach
        configs["with_headers"] = {
            "model": "moonshotai/kimi-k2-0905",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "model_api_key": self.openrouter_key,
            "context_window": 200000,
            "model_wrapper": None,
            "extra_headers": {
                "HTTP-Referer": "https://atlas.local",
                "X-Title": "ATLAS Multi-Agent System"
            }
        }

        # Test 5: Cerebras Model (different provider)
        configs["cerebras_model"] = {
            "model": "qwen/qwen3-235b-a22b-thinking-2507",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "model_api_key": self.openrouter_key,
            "context_window": 32768
        }

        # Test 6: Sambanova Model
        configs["sambanova_model"] = {
            "model": "deepseek/deepseek-chat-v3.1",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "model_api_key": self.openrouter_key,
            "context_window": 64000
        }

        # Test 7: With model wrapper
        configs["with_wrapper"] = {
            "model": "moonshotai/kimi-k2-0905",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "model_api_key": self.openrouter_key,
            "model_wrapper": "chatml",  # Try different wrapper
            "context_window": 200000
        }

        # Test 8: Without context window
        configs["no_context_window"] = {
            "model": "moonshotai/kimi-k2-0905",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "model_api_key": self.openrouter_key
        }

        # Test 9: With Bearer prefix in API key
        configs["bearer_prefix"] = {
            "model": "moonshotai/kimi-k2-0905",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "model_api_key": f"Bearer {self.openrouter_key}",
            "context_window": 200000
        }

        # Test 10: Using OpenRouterConfig class
        or_config = OpenRouterConfig.get_llm_config(model_priority=0, api_key=self.openrouter_key)
        configs["openrouter_config_class"] = or_config

        return configs

    async def test_configuration(self, config_name: str, llm_config_dict: Dict[str, Any]) -> TestResult:
        """Test a single LLM configuration."""
        result = TestResult(config_name=config_name, success=False)
        agent = None

        print(f"\n{'='*50}")
        print(f"Testing: {config_name}")
        print(f"{'='*50}")

        try:
            # Create LLM config
            llm_config = LLMConfig(**llm_config_dict)
            print(f"Model: {llm_config.model}")
            print(f"Endpoint: {llm_config.model_endpoint}")

            # Create agent
            print("Creating agent...")
            agent = self.client.agents.create(
                name=f"test_{config_name}_{datetime.now().strftime('%H%M%S')}",
                description=f"Test agent for {config_name} configuration",
                system="You are a test agent. Always respond concisely.",
                llm_config=llm_config,
                embedding_config=self.get_embedding_config()
            )
            result.agent_created = True
            print(f"✅ Agent created: {agent.id[:8]}...")

            # Send test message
            print("Sending test message...")
            response = self.client.agents.messages.create(
                agent_id=agent.id,
                messages=[{
                    "role": "user",
                    "content": "Say 'Configuration working!' in exactly three words"
                }]
            )
            result.message_sent = True
            print("✅ Message sent")

            # Check response
            if response and response.messages:
                result.response_received = True
                for msg in response.messages:
                    if hasattr(msg, 'content') and msg.content:
                        result.response_content = msg.content[:200]
                        print(f"✅ Response: {msg.content[:100]}...")
                        break
                    elif hasattr(msg, 'text') and msg.text:
                        result.response_content = msg.text[:200]
                        print(f"✅ Response: {msg.text[:100]}...")
                        break

                result.success = True
                result.model_used = llm_config.model
                print(f"🎉 SUCCESS: {config_name} configuration works!")

        except Exception as e:
            result.error = str(e)
            result.error_type = type(e).__name__
            print(f"❌ Failed: {result.error_type}: {str(e)[:200]}")

        finally:
            # Clean up agent
            if agent and result.agent_created:
                try:
                    self.client.agents.delete(agent.id)
                    print("🧹 Agent cleaned up")
                except:
                    pass

        return result

    async def test_provider_routing(self) -> List[TestResult]:
        """Test provider routing with different models."""
        print("\n" + "="*60)
        print("  Testing Provider Routing")
        print("="*60)

        provider_tests = []

        # Test Groq provider
        groq_result = await self.test_configuration(
            "groq_provider",
            {
                "model": "moonshotai/kimi-k2-0905",
                "model_endpoint_type": "openai",
                "model_endpoint": "https://openrouter.ai/api/v1",
                "model_api_key": self.openrouter_key,
                "context_window": 200000
            }
        )
        provider_tests.append(groq_result)

        # Test Cerebras provider
        cerebras_result = await self.test_configuration(
            "cerebras_provider",
            {
                "model": "qwen/qwen3-235b-a22b-thinking-2507",
                "model_endpoint_type": "openai",
                "model_endpoint": "https://openrouter.ai/api/v1",
                "model_api_key": self.openrouter_key,
                "context_window": 32768
            }
        )
        provider_tests.append(cerebras_result)

        # Test Sambanova provider
        sambanova_result = await self.test_configuration(
            "sambanova_provider",
            {
                "model": "deepseek/deepseek-chat-v3.1",
                "model_endpoint_type": "openai",
                "model_endpoint": "https://openrouter.ai/api/v1",
                "model_api_key": self.openrouter_key,
                "context_window": 64000
            }
        )
        provider_tests.append(sambanova_result)

        return provider_tests

    async def run_all_tests(self):
        """Run all configuration tests."""
        if not self.setup():
            return

        # Test all configurations
        configs = self.get_test_configurations()

        print(f"\n📋 Testing {len(configs)} configurations...")

        for config_name, config_dict in configs.items():
            result = await self.test_configuration(config_name, config_dict)
            self.results.append(result)

        # Test provider routing
        provider_results = await self.test_provider_routing()
        self.results.extend(provider_results)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "="*60)
        print("  Test Results Summary")
        print("="*60 + "\n")

        successful_configs = []
        failed_configs = []

        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.config_name:30}")

            if result.success:
                successful_configs.append(result.config_name)
                print(f"   - Agent created: {result.agent_created}")
                print(f"   - Message sent: {result.message_sent}")
                print(f"   - Response received: {result.response_received}")
                if result.response_content:
                    print(f"   - Response: {result.response_content[:50]}...")
            else:
                failed_configs.append(result.config_name)
                print(f"   - Agent created: {result.agent_created}")
                print(f"   - Message sent: {result.message_sent}")
                print(f"   - Error: {result.error_type}: {result.error[:100] if result.error else 'Unknown'}")

        print(f"\n📊 Results: {len(successful_configs)}/{len(self.results)} configurations successful")

        if successful_configs:
            print("\n✅ Working Configurations:")
            for config in successful_configs:
                print(f"   - {config}")

            # Find the best configuration
            print("\n🎯 RECOMMENDED CONFIGURATION:")
            if "standard_openrouter" in successful_configs:
                print("   Use standard OpenRouter configuration (no prefix)")
            elif "with_prefix" in successful_configs:
                print("   Use openrouter/ prefix in model name")
            elif successful_configs:
                print(f"   Use {successful_configs[0]} configuration")

        if failed_configs:
            print("\n❌ Failed Configurations:")
            for config in failed_configs:
                result = next(r for r in self.results if r.config_name == config)
                print(f"   - {config}: {result.error_type}")

        # Check provider routing
        print("\n🔀 Provider Routing Results:")
        for provider in ["groq_provider", "cerebras_provider", "sambanova_provider"]:
            result = next((r for r in self.results if r.config_name == provider), None)
            if result:
                status = "✅" if result.success else "❌"
                print(f"   {status} {provider}: {'Working' if result.success else 'Failed'}")


async def main():
    """Main test runner."""
    tester = OpenRouterConfigTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())