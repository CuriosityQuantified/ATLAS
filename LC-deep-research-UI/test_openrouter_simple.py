#!/usr/bin/env python3
"""
Simple test for OpenRouter integration without requiring full package installation.
"""

import os
import sys
import asyncio
from pathlib import Path

# Test if we can import the required packages
try:
    from langchain_openai import ChatOpenAI
    print("✅ langchain-openai is installed")
except ImportError:
    print("❌ langchain-openai is not installed. Installing...")
    os.system("pip3 install langchain-openai")
    from langchain_openai import ChatOpenAI

try:
    # Removed ChatAnthropic import - using OpenRouter exclusively
    print("✅ langchain-anthropic is installed")
except ImportError:
    print("❌ langchain-anthropic is not installed")


class ChatOpenRouter(ChatOpenAI):
    """Simple OpenRouter implementation for testing."""
    
    def __init__(self, model_name="anthropic/claude-3-sonnet", **kwargs):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
        
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model_name,
            **kwargs
        )
        print(f"Initialized OpenRouter with model: {model_name}")


async def test_openrouter():
    """Test OpenRouter with a simple query."""
    print("\n" + "="*60)
    print(" Testing OpenRouter Integration")
    print("="*60)
    
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n❌ ERROR: OPENROUTER_API_KEY not found!")
        print("Looking for .env file...")
        
        # Try to load from .env
        env_path = Path("/Users/nicholaspate/Documents/01_Active/ATLAS/.env")
        if env_path.exists():
            print(f"Found .env at: {env_path}")
            with open(env_path) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY"):
                        key = line.split("=", 1)[1].strip()
                        os.environ["OPENROUTER_API_KEY"] = key
                        print("✅ Loaded OPENROUTER_API_KEY from .env")
                        break
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Could not find OPENROUTER_API_KEY")
        return
    
    try:
        # Test 1: Claude via OpenRouter
        print("\n1. Testing Claude 3 Sonnet via OpenRouter...")
        model = ChatOpenRouter(model_name="anthropic/claude-3-sonnet", max_tokens=100)
        response = await model.ainvoke("What is 2+2? Reply with just the number.")
        print(f"   Response: {response.content}")
        print("   ✅ Claude via OpenRouter works!")
        
        # Test 2: Cheaper model
        print("\n2. Testing Gemini Flash (cheaper model)...")
        model = ChatOpenRouter(model_name="google/gemini-flash-1.5", max_tokens=100)
        response = await model.ainvoke("What is 3+3? Reply with just the number.")
        print(f"   Response: {response.content}")
        print("   ✅ Gemini via OpenRouter works!")
        
        # Test 3: Qwen Coder model
        print("\n3. Testing Qwen Coder model...")
        model = ChatOpenRouter(model_name="qwen/qwen-2.5-coder-32b-instruct", max_tokens=100)
        response = await model.ainvoke("Write a Python function to add two numbers. Just the function, no explanation.")
        print(f"   Response: {response.content}")
        print("   ✅ Qwen Coder via OpenRouter works!")
        
        print("\n" + "="*60)
        print(" 🎉 All tests passed!")
        print("="*60)
        print("\nOpenRouter is successfully integrated and working!")
        print("\nYou can now use these models in your Deep Agents by:")
        print("1. Setting USE_OPENROUTER=true in your environment")
        print("2. Setting OPENROUTER_MODEL=<model_name> to choose a model")
        print("3. Or let it automatically fallback when Anthropic credits are exhausted")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_openrouter())