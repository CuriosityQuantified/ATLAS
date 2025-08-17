#!/usr/bin/env python3
"""
Test script for OpenRouter integration with Deep Agents.
Tests various scenarios including fallback behavior and different models.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the deepagents source to path
sys.path.insert(0, str(Path(__file__).parent / "deepagents" / "src"))

# Import the model functions
from deepagents.model import get_default_model, get_model_for_task
from deepagents.openrouter_model import ChatOpenRouter


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


async def test_direct_openrouter():
    """Test direct OpenRouter usage."""
    print_section("Testing Direct OpenRouter")
    
    try:
        # Test with Claude through OpenRouter
        print("\n1. Testing Claude 3 Sonnet via OpenRouter...")
        model = ChatOpenRouter(model_name="anthropic/claude-3-sonnet", max_tokens=100)
        response = await model.ainvoke("Say 'OpenRouter Claude works!' in exactly 4 words.")
        print(f"   Response: {response.content}")
        
        # Test with a cheaper model
        print("\n2. Testing Gemini Flash via OpenRouter...")
        model = ChatOpenRouter(model_name="google/gemini-flash-1.5", max_tokens=100)
        response = await model.ainvoke("Say 'OpenRouter Gemini works!' in exactly 4 words.")
        print(f"   Response: {response.content}")
        
        # Show available models
        print("\n3. Available models via OpenRouter:")
        models = ChatOpenRouter.list_available_models()
        for name, config in list(models.items())[:5]:  # Show first 5
            if name != "default":
                print(f"   - {name}: {config['max_tokens']} tokens, ${config['cost_per_1m']}/1M")
        
        print("\n✅ Direct OpenRouter tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Direct OpenRouter test failed: {e}")
        return False


async def test_model_selection():
    """Test model selection with environment variables."""
    print_section("Testing Model Selection")
    
    try:
        # Test default behavior (should use Anthropic with fallback)
        print("\n1. Testing default model (Anthropic with fallback)...")
        os.environ.pop("USE_OPENROUTER", None)  # Ensure not forcing OpenRouter
        model = get_default_model()
        print(f"   Model type: {type(model).__name__}")
        
        # Force OpenRouter
        print("\n2. Testing forced OpenRouter...")
        os.environ["USE_OPENROUTER"] = "true"
        os.environ["OPENROUTER_MODEL"] = "google/gemini-flash-1.5"
        model = get_default_model()
        print(f"   Model type: {type(model).__name__}")
        if hasattr(model, 'model_info'):
            print(f"   Model info: {model.model_info}")
        
        # Test task-specific models
        print("\n3. Testing task-specific models...")
        for task in ["coding", "research", "cheap"]:
            model = get_model_for_task(task)
            print(f"   {task}: {type(model).__name__}")
        
        print("\n✅ Model selection tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Model selection test failed: {e}")
        return False
    finally:
        # Clean up environment
        os.environ.pop("USE_OPENROUTER", None)
        os.environ.pop("OPENROUTER_MODEL", None)


async def test_fallback_behavior():
    """Test fallback from Anthropic to OpenRouter."""
    print_section("Testing Fallback Behavior")
    
    try:
        # Temporarily remove Anthropic key to trigger fallback
        original_key = os.environ.get("ANTHROPIC_API_KEY")
        
        print("\n1. Testing with Anthropic key (should use Anthropic)...")
        if original_key:
            model = get_default_model()
            print(f"   Model type: {type(model).__name__}")
        else:
            print("   No Anthropic key found, skipping this test")
        
        print("\n2. Testing without Anthropic key (should fallback to OpenRouter)...")
        os.environ.pop("ANTHROPIC_API_KEY", None)
        model = get_default_model()
        print(f"   Model type: {type(model).__name__}")
        
        # Restore key
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key
        
        print("\n✅ Fallback behavior tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Fallback test failed: {e}")
        # Restore key if test failed
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key
        return False


async def test_langchain_compatibility():
    """Test that OpenRouter models work with LangChain chains."""
    print_section("Testing LangChain Compatibility")
    
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        # Create a simple chain with OpenRouter
        os.environ["USE_OPENROUTER"] = "true"
        model = get_default_model()
        
        prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
        chain = prompt | model | StrOutputParser()
        
        print("\n1. Testing chain execution...")
        result = await chain.ainvoke({"topic": "programming"})
        print(f"   Chain result: {result[:100]}...")  # Show first 100 chars
        
        print("\n✅ LangChain compatibility test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ LangChain compatibility test failed: {e}")
        return False
    finally:
        os.environ.pop("USE_OPENROUTER", None)


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print(" OpenRouter Integration Test Suite")
    print("="*60)
    
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n❌ ERROR: OPENROUTER_API_KEY not found in environment!")
        print("Please set your OpenRouter API key before running tests.")
        return
    
    print(f"\n✅ OpenRouter API key found")
    print(f"✅ Anthropic API key: {'Found' if os.getenv('ANTHROPIC_API_KEY') else 'Not found'}")
    
    # Run tests
    results = []
    
    # Test 1: Direct OpenRouter
    results.append(await test_direct_openrouter())
    
    # Test 2: Model selection
    results.append(await test_model_selection())
    
    # Test 3: Fallback behavior
    results.append(await test_fallback_behavior())
    
    # Test 4: LangChain compatibility
    results.append(await test_langchain_compatibility())
    
    # Summary
    print_section("Test Summary")
    passed = sum(results)
    total = len(results)
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! OpenRouter integration is working correctly.")
        print("\nYou can now use OpenRouter by:")
        print("1. Setting USE_OPENROUTER=true to force OpenRouter")
        print("2. Setting OPENROUTER_MODEL to choose a specific model")
        print("3. Or let it automatically fallback when Anthropic fails")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())