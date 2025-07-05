#!/usr/bin/env python3
"""
Test script to demonstrate LLM logging functionality in ATLAS
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.call_model import CallModel
from agents.global_supervisor import GlobalSupervisorAgent
from agents.base import Task


async def test_direct_llm_call():
    """Test direct LLM call logging"""
    print("\n" + "="*80)
    print("TEST 1: Direct LLM Call with CallModel")
    print("="*80)
    
    # Create CallModel instance
    call_model = CallModel(
        task_id="test_task_001",
        agent_id="test_agent"
    )
    
    # Make a simple call
    response = await call_model.call_model(
        model_name="claude-3-5-haiku-20241022",
        system_prompt="You are a helpful AI assistant testing the ATLAS logging system.",
        most_recent_message="Please respond with 'ATLAS logging test successful!' to confirm the logging is working.",
        max_tokens=100,
        temperature=0.7
    )
    
    print(f"\nResponse received: {response.content[:100]}...")
    print(f"Success: {response.success}")
    print(f"Tokens: {response.total_tokens}")
    print(f"Cost: ${response.cost_usd:.4f}" if response.cost_usd else "Cost: N/A")
    
    return response


async def test_global_supervisor_call():
    """Test Global Supervisor with Letta memory logging"""
    print("\n" + "="*80)
    print("TEST 2: Global Supervisor with Letta Memory")
    print("="*80)
    
    # Create Global Supervisor
    supervisor = GlobalSupervisorAgent(
        task_id="test_task_002"
    )
    
    # Create a test task
    task = Task(
        task_id="test_task_002",
        task_type="research_analysis",
        description="Research the latest developments in quantum computing and provide a brief summary.",
        priority="medium",
        context={
            "requester": "test_script",
            "purpose": "logging_demonstration"
        }
    )
    
    # Process the task
    print("\nProcessing task through Global Supervisor...")
    result = await supervisor.process_task(task)
    
    print(f"\nTask Result:")
    print(f"Success: {result.success}")
    print(f"Result Type: {result.result_type}")
    print(f"Processing Time: {result.processing_time:.2f}s")
    
    return result


async def test_error_logging():
    """Test error logging"""
    print("\n" + "="*80)
    print("TEST 3: Error Logging")
    print("="*80)
    
    call_model = CallModel(
        task_id="test_task_003",
        agent_id="test_error_agent"
    )
    
    # Make a call with invalid model name to trigger error
    response = await call_model.call_model(
        model_name="invalid-model-name-xyz",
        most_recent_message="This should fail",
        max_tokens=100
    )
    
    print(f"\nError Response:")
    print(f"Success: {response.success}")
    print(f"Error: {response.error}")
    print(f"Error Type: {response.error_type}")
    
    return response


async def main():
    """Run all tests"""
    print(f"\nATLAS LLM Logging Test Suite")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"\nLog files will be created in: ./logs/")
    print(f"Look for:")
    print(f"  - llm_calls_{datetime.now().strftime('%Y%m%d')}.log")
    print(f"  - letta_llm_calls_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Ensure log directory exists
    os.makedirs('./logs', exist_ok=True)
    
    try:
        # Test 1: Direct LLM call
        await test_direct_llm_call()
        
        # Test 2: Global Supervisor call
        await test_global_supervisor_call()
        
        # Test 3: Error logging
        await test_error_logging()
        
        print("\n" + "="*80)
        print("All tests completed! Check the log files for detailed LLM interactions.")
        print("="*80)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())