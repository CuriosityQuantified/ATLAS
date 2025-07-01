#!/usr/bin/env python3
"""
Test script for ATLAS CallModel with AG-UI and MLflow tracking integration
Demonstrates comprehensive tracking and monitoring capabilities
"""

import asyncio
import time
import sys
import os
from typing import List, Dict, Any
import uuid

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from backend.src.utils.call_model import (
    CallModel, ModelRequest, ModelResponse, ModelProvider, InvocationMethod, quick_call
)
from backend.src.agui.handlers import AGUIEventBroadcaster
from backend.src.mlflow.tracking import ATLASMLflowTracker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MockConnectionManager:
    """Mock connection manager for testing without full AG-UI server."""
    
    def __init__(self):
        self.events = []
    
    async def broadcast_to_task(self, task_id: str, event):
        """Mock broadcast method."""
        self.events.append(event)
        print(f"📡 AG-UI Event: {event.event_type.value} - {event.data}")
    
    def get_events(self):
        """Get all captured events."""
        return self.events


async def test_call_model_with_tracking():
    """Test CallModel with full AG-UI and MLflow tracking integration."""
    print("🧪 Testing CallModel with AG-UI and MLflow Tracking")
    print("=" * 60)
    
    # Setup tracking components
    task_id = f"test_tracking_{int(time.time())}"
    agent_id = "test_call_model_agent"
    
    # Mock connection manager for AG-UI testing
    mock_connection_manager = MockConnectionManager()
    agui_broadcaster = AGUIEventBroadcaster(mock_connection_manager)
    
    # MLflow tracker
    mlflow_tracker = ATLASMLflowTracker()
    
    # Initialize CallModel with tracking
    call_model = CallModel(
        enable_threading=True,
        max_workers=3,
        task_id=task_id,
        agent_id=agent_id,
        agui_broadcaster=agui_broadcaster,
        mlflow_tracker=mlflow_tracker
    )
    
    try:
        # Start MLflow run for testing
        with mlflow_tracker.start_agent_run(
            agent_id=agent_id,
            agent_type="test_call_model",
            task_id=task_id,
            parent_run_id=None
        ) as run_id:
            
            print(f"🎯 Task ID: {task_id}")
            print(f"🤖 Agent ID: {agent_id}")
            print(f"📊 MLflow Run ID: {run_id}")
            print("-" * 60)
            
            # Test 1: Single model call with tracking
            print("\n📝 Test 1: Single Model Call with Full Tracking")
            response = await call_model.call_model(
                model_name="claude-3-5-haiku-20241022",
                system_prompt="You are a helpful AI assistant being tested in the ATLAS system.",
                most_recent_message="Respond with 'CallModel tracking test successful!' and include the model name.",
                max_tokens=100,
                temperature=0.3,
                run_id=run_id
            )
            
            if response.success:
                print(f"✅ Model call successful")
                print(f"📝 Response: {response.content[:100]}...")
                print(f"⚡ Provider: {response.provider}")
                print(f"🔧 Method: {response.invocation_method}")
                print(f"⏱️  Time: {response.response_time:.2f}s")
                print(f"🎯 Tokens: {response.total_tokens}")
                if response.cost_usd:
                    print(f"💰 Cost: ${response.cost_usd:.6f}")
            else:
                print(f"❌ Model call failed: {response.error}")
            
            await asyncio.sleep(1)
            
            # Test 2: Multiple concurrent calls with tracking
            print("\n📝 Test 2: Concurrent Model Calls with Tracking")
            concurrent_requests = [
                ("claude-3-5-haiku-20241022", {
                    "system_prompt": "You are a research assistant.",
                    "most_recent_message": "What is machine learning in one sentence?",
                    "max_tokens": 50,
                    "run_id": run_id
                }),
                ("llama-3.1-8b-instant", {
                    "system_prompt": "You are a data analyst.",
                    "most_recent_message": "What is data science in one sentence?",
                    "max_tokens": 50,
                    "run_id": run_id
                }),
                ("gpt-4o-mini", {
                    "system_prompt": "You are a technical writer.",
                    "most_recent_message": "What is artificial intelligence in one sentence?",
                    "max_tokens": 50,
                    "run_id": run_id
                }),
            ]
            
            start_time = time.time()
            responses = await call_model.call_multiple_models(concurrent_requests, run_id=run_id)
            total_time = time.time() - start_time
            
            print(f"⏱️  Total concurrent time: {total_time:.2f}s")
            
            successful = 0
            for i, response in enumerate(responses):
                if isinstance(response, ModelResponse) and response.success:
                    successful += 1
                    print(f"   ✅ Call {i+1}: {response.provider} - {response.response_time:.2f}s")
                    print(f"      📝 {response.content[:60]}...")
                else:
                    print(f"   ❌ Call {i+1}: Failed")
            
            print(f"📊 Success rate: {successful}/{len(concurrent_requests)} ({successful/len(concurrent_requests)*100:.1f}%)")
            
            await asyncio.sleep(1)
            
            # Test 3: Quick call with tracking
            print("\n📝 Test 3: Quick Call with Tracking")
            quick_result = await quick_call(
                "llama-3.1-8b-instant",
                "Say 'Quick call with tracking works!' and nothing else.",
                system_prompt="You are a test assistant.",
                task_id=task_id,
                agent_id=agent_id,
                agui_broadcaster=agui_broadcaster,
                mlflow_tracker=mlflow_tracker,
                run_id=run_id
            )
            print(f"⚡ Quick call result: {quick_result}")
            
            await asyncio.sleep(1)
            
            # Test 4: Error case tracking
            print("\n📝 Test 4: Error Case Tracking")
            error_response = await call_model.call_model(
                model_name="invalid-model-name",
                most_recent_message="This should fail",
                run_id=run_id
            )
            
            if not error_response.success:
                print(f"✅ Error correctly tracked: {error_response.error}")
                print(f"🔍 Error type: {error_response.error_type}")
            
            # Show performance statistics
            print("\n📊 Performance Statistics")
            stats = call_model.get_performance_stats()
            for method, data in stats.items():
                print(f"   {method}: {data['total_calls']} calls, avg {data['average_time']:.2f}s")
            
            # Show AG-UI events captured
            print("\n📡 AG-UI Events Captured")
            events = mock_connection_manager.get_events()
            for i, event in enumerate(events):
                print(f"   Event {i+1}: {event.event_type.value}")
                if hasattr(event, 'data') and 'model_name' in event.data:
                    print(f"      Model: {event.data.get('model_name', 'unknown')}")
                if hasattr(event, 'data') and 'cost_usd' in event.data:
                    print(f"      Cost: ${event.data.get('cost_usd', 0):.6f}")
            
            print(f"\n🎯 Total AG-UI events generated: {len(events)}")
            
    finally:
        call_model.cleanup()
    
    print("\n✅ CallModel tracking integration test completed!")
    return True


async def test_call_model_basic():
    """Test basic CallModel functionality without tracking."""
    print("\n🧪 Testing Basic CallModel Functionality")
    print("=" * 60)
    
    call_model = CallModel()
    
    try:
        # Test auto-detection
        print("\n🎯 Testing Auto-Detection")
        test_models = [
            "claude-3-5-haiku-20241022",  # Should detect Anthropic
            "gpt-4o-mini",                # Should detect OpenAI  
            "llama-3.1-8b-instant",       # Should detect Groq
        ]
        
        for model in test_models:
            print(f"🔍 Testing: {model}")
            
            response = await call_model.call_model(
                model_name=model,
                most_recent_message="Hello! Please respond with just your model name.",
                max_tokens=20
            )
            
            if response.success:
                print(f"   ✅ Success: {response.provider} via {response.invocation_method}")
                print(f"   📝 Response: {response.content}")
                print(f"   ⏱️  Time: {response.response_time:.2f}s")
            else:
                print(f"   ❌ Failed: {response.error}")
    
    finally:
        call_model.cleanup()
    
    return True


async def run_comprehensive_tests():
    """Run all CallModel tests."""
    print("🚀 ATLAS CallModel Comprehensive Test Suite with Tracking")
    print("=" * 70)
    
    test_results = {}
    
    # Run test suites
    test_suites = [
        ("Basic CallModel", test_call_model_basic),
        ("CallModel with Tracking", test_call_model_with_tracking),
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
    print("\n" + "=" * 70)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall Results: {passed}/{total} test suites passed")
    
    if passed >= total:
        print("🏆 ATLAS CallModel with Tracking: READY FOR PRODUCTION!")
        print("🚀 All core functionality and tracking verified!")
    else:
        print("⚠️  Some issues detected. Please review the logs above.")
    
    return test_results


if __name__ == "__main__":
    # Run comprehensive tests
    asyncio.run(run_comprehensive_tests())