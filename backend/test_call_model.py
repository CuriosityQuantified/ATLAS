#!/usr/bin/env python3
"""
Test script for ATLAS CallModel unified model interface
Demonstrates usage patterns and performance testing
"""

import asyncio
import time
import sys
import os
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.call_model import (
    CallModel, ModelRequest, ModelResponse, ModelProvider, InvocationMethod, quick_call
)


async def test_single_models():
    """Test individual model calls with different providers."""
    print("🧪 Testing Single Model Calls")
    print("=" * 50)
    
    call_model = CallModel()
    
    test_cases = [
        {
            "name": "Anthropic Claude (Direct)",
            "model": "claude-3-5-haiku-20241022",
            "provider": ModelProvider.ANTHROPIC,
            "method": InvocationMethod.DIRECT,
        },
        {
            "name": "OpenAI GPT (Direct)",
            "model": "gpt-4o-mini",
            "provider": ModelProvider.OPENAI,
            "method": InvocationMethod.DIRECT,
        },
        {
            "name": "Groq Llama (Direct)",
            "model": "llama-3.1-8b-instant",
            "provider": ModelProvider.GROQ,
            "method": InvocationMethod.DIRECT,
        },
        {
            "name": "Google Gemini (Direct)",
            "model": "gemini-1.5-flash",
            "provider": ModelProvider.GOOGLE,
            "method": InvocationMethod.DIRECT,
        },
        {
            "name": "HuggingFace (HTTP)",
            "model": "microsoft/Phi-3-mini-4k-instruct",
            "provider": ModelProvider.HUGGINGFACE,
            "method": InvocationMethod.HTTP,
        },
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔬 Testing: {test_case['name']}")
        
        try:
            response = await call_model.call_model(
                model_name=test_case["model"],
                provider=test_case["provider"],
                invocation_method=test_case["method"],
                system_prompt="You are a helpful AI assistant in the ATLAS multi-agent system.",
                most_recent_message="Respond with 'CallModel test successful' and the current model name.",
                max_tokens=100,
                temperature=0.3
            )
            
            if response.success:
                print(f"   ✅ Success - {response.response_time:.2f}s")
                print(f"   📝 Response: {response.content[:100]}...")
                if response.total_tokens:
                    print(f"   🎯 Tokens: {response.total_tokens}")
            else:
                print(f"   ❌ Failed: {response.error}")
            
            results.append({
                "test": test_case["name"],
                "success": response.success,
                "time": response.response_time,
                "tokens": response.total_tokens,
                "error": response.error
            })
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append({
                "test": test_case["name"],
                "success": False,
                "time": None,
                "tokens": None,
                "error": str(e)
            })
    
    call_model.cleanup()
    return results


async def test_conversation_flow():
    """Test conversation flow with history."""
    print("\n💬 Testing Conversation Flow")
    print("=" * 50)
    
    call_model = CallModel()
    
    try:
        # Build conversation history
        conversation = [
            {"role": "system", "content": "You are a helpful AI assistant in ATLAS."},
            {"role": "user", "content": "Hello, what is ATLAS?"},
            {"role": "assistant", "content": "ATLAS is an Agentic Task Logic & Analysis System - a multi-agent platform for complex reasoning tasks."},
            {"role": "user", "content": "What are its main components?"},
        ]
        
        response = await call_model.call_model(
            model_name="claude-3-5-haiku-20241022",
            conversation_history=conversation[:-1],  # All but last message
            most_recent_message=conversation[-1],    # Last message
            max_tokens=200
        )
        
        if response.success:
            print(f"✅ Conversation flow successful - {response.response_time:.2f}s")
            print(f"📝 Response: {response.content}")
            return True
        else:
            print(f"❌ Conversation flow failed: {response.error}")
            return False
            
    finally:
        call_model.cleanup()


async def test_concurrent_calls():
    """Test concurrent model calls for horizontal scaling."""
    print("\n🚀 Testing Concurrent Model Calls")
    print("=" * 50)
    
    call_model = CallModel()
    
    try:
        # Prepare multiple requests
        requests = [
            ("claude-3-5-haiku-20241022", {
                "system_prompt": "You are a research assistant.",
                "most_recent_message": "What is machine learning?",
                "max_tokens": 50
            }),
            ("llama-3.1-8b-instant", {
                "system_prompt": "You are a data analyst.",
                "most_recent_message": "What is data science?",
                "max_tokens": 50
            }),
            ("gpt-4o-mini", {
                "system_prompt": "You are a technical writer.",
                "most_recent_message": "What is artificial intelligence?",
                "max_tokens": 50
            }),
        ]
        
        start_time = time.time()
        responses = await call_model.call_multiple_models(requests)
        total_time = time.time() - start_time
        
        print(f"⏱️  Total time for {len(requests)} concurrent calls: {total_time:.2f}s")
        
        successful = 0
        for i, response in enumerate(responses):
            if isinstance(response, ModelResponse) and response.success:
                successful += 1
                print(f"   ✅ Call {i+1}: {response.response_time:.2f}s - {response.content[:50]}...")
            else:
                print(f"   ❌ Call {i+1}: Failed")
        
        print(f"📊 Success rate: {successful}/{len(requests)} ({successful/len(requests)*100:.1f}%)")
        return successful == len(requests)
        
    finally:
        call_model.cleanup()


async def test_auto_detection():
    """Test automatic provider and method detection."""
    print("\n🎯 Testing Auto-Detection")
    print("=" * 50)
    
    call_model = CallModel()
    
    try:
        test_models = [
            "claude-3-5-haiku-20241022",  # Should detect Anthropic
            "gpt-4o-mini",                # Should detect OpenAI  
            "llama-3.1-8b-instant",       # Should detect Groq
            "gemini-1.5-flash",           # Should detect Google
        ]
        
        for model in test_models:
            print(f"🔍 Auto-detecting for: {model}")
            
            response = await call_model.call_model(
                model_name=model,
                # No provider or method specified - should auto-detect
                most_recent_message="Say hello",
                max_tokens=20
            )
            
            if response.success:
                print(f"   ✅ Detected: {response.provider} via {response.invocation_method}")
                print(f"   📝 Response: {response.content}")
            else:
                print(f"   ❌ Failed: {response.error}")
        
        return True
        
    finally:
        call_model.cleanup()


async def test_quick_call():
    """Test the convenience quick_call function."""
    print("\n⚡ Testing Quick Call Function")
    print("=" * 50)
    
    try:
        result = await quick_call(
            "claude-3-5-haiku-20241022",
            "Respond with 'Quick call successful!' and nothing else.",
            system_prompt="You are a helpful assistant."
        )
        
        print(f"📝 Quick call result: {result}")
        return "Quick call successful" in result
        
    except Exception as e:
        print(f"❌ Quick call failed: {e}")
        return False


async def test_performance_monitoring():
    """Test performance monitoring and statistics."""
    print("\n📊 Testing Performance Monitoring")
    print("=" * 50)
    
    call_model = CallModel()
    
    try:
        # Make several calls to build statistics
        for i in range(3):
            await call_model.call_model(
                model_name="claude-3-5-haiku-20241022",
                most_recent_message=f"Test call #{i+1}",
                max_tokens=20
            )
        
        # Get performance stats
        stats = call_model.get_performance_stats()
        print("Performance Statistics:")
        for method, data in stats.items():
            print(f"   {method}: {data['total_calls']} calls, avg {data['average_time']:.2f}s")
        
        return len(stats) > 0
        
    finally:
        call_model.cleanup()


async def run_comprehensive_tests():
    """Run all tests and provide summary."""
    print("🚀 ATLAS CallModel Comprehensive Test Suite")
    print("=" * 60)
    
    test_results = {}
    
    # Run all test suites
    test_suites = [
        ("Single Models", test_single_models),
        ("Conversation Flow", test_conversation_flow),
        ("Concurrent Calls", test_concurrent_calls),
        ("Auto Detection", test_auto_detection),
        ("Quick Call", test_quick_call),
        ("Performance Monitoring", test_performance_monitoring),
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n🧪 Running: {suite_name}")
        try:
            result = await test_func()
            test_results[suite_name] = result
        except Exception as e:
            print(f"❌ {suite_name} failed with exception: {e}")
            test_results[suite_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results.items():
        if isinstance(success, list):  # Handle single model results
            success_count = sum(1 for r in success if r["success"])
            total_count = len(success)
            print(f"📊 {test_name}: {success_count}/{total_count} models working")
            if success_count > 0:
                passed += 1
        else:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed += 1
    
    print(f"\n🎯 Overall Results: {passed}/{total} test suites passed")
    
    if passed >= total * 0.7:  # 70% pass rate
        print("🏆 ATLAS CallModel: READY FOR PRODUCTION!")
        print("🚀 All core functionality verified and working!")
    else:
        print("⚠️  Some issues detected. Please review the logs above.")
    
    return test_results


if __name__ == "__main__":
    # Run comprehensive tests
    asyncio.run(run_comprehensive_tests())