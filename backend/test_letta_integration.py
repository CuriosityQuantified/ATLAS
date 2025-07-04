#!/usr/bin/env python3
"""
Test script for Letta integration with Global Supervisor
Tests basic flow without requiring full system setup
"""

import asyncio
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/nicholaspate/Documents/ATLAS/.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add backend to path
import sys
sys.path.append('/Users/nicholaspate/Documents/ATLAS/backend')

from src.agents.global_supervisor import GlobalSupervisorAgent
from src.agents.base import Task

async def test_basic_letta_flow():
    """Test basic Letta integration with Global Supervisor"""
    
    print("\n🧪 Testing Letta Integration with Global Supervisor")
    print("=" * 60)
    
    try:
        # Create Global Supervisor instance
        print("\n1️⃣ Creating Global Supervisor agent...")
        supervisor = GlobalSupervisorAgent(
            task_id="test_letta_001"
        )
        print(f"✅ Created supervisor: {supervisor.agent_id}")
        
        # Create a test task
        print("\n2️⃣ Creating test task...")
        task = Task(
            task_id="test_letta_001",
            task_type="research_and_analysis",
            description="What are the latest developments in quantum computing and how might they impact cryptography in the next 5 years?",
            priority="high",
            assigned_to="global_supervisor",
            created_at=datetime.now(),
            context={
                "focus_areas": ["quantum supremacy", "post-quantum cryptography", "commercial applications"],
                "output_format": "executive summary"
            }
        )
        print(f"✅ Created task: {task.task_id}")
        print(f"   Description: {task.description[:80]}...")
        
        # Process the task
        print("\n3️⃣ Processing task with Letta agent...")
        print("   (This may take a moment while Letta initializes...)")
        
        result = await supervisor.process_task(task)
        
        # Display results
        print("\n4️⃣ Task processing complete!")
        print(f"   Success: {result.success}")
        print(f"   Result type: {result.result_type}")
        print(f"   Processing time: {result.processing_time:.2f} seconds")
        
        if result.success:
            content = result.content
            
            if result.result_type == "tool_calls_needed":
                print("\n📞 Tool Calls Detected:")
                print(f"   Reasoning: {content.get('reasoning', '')[:200]}...")
                print(f"\n   Tool calls needed ({len(content.get('tool_calls', []))}):")
                
                for i, tool_call in enumerate(content.get('tool_calls', []), 1):
                    print(f"   {i}. {tool_call.get('name')}")
                    print(f"      Arguments: {tool_call.get('arguments')}")
                    
                print(f"\n   Next step: {content.get('next_step')}")
                
            elif result.result_type == "global_coordination":
                print("\n📝 Direct Response (No tools needed):")
                print(f"   Analysis: {content.get('deliverables', {}).get('analysis', '')[:300]}...")
                
            # Check metadata
            if result.metadata:
                print("\n📊 Metadata:")
                print(f"   Letta agent ID: {result.metadata.get('letta_agent_id')}")
                print(f"   Memory enabled: {result.metadata.get('memory_enabled')}")
                print(f"   Tool count: {result.metadata.get('tool_count', 0)}")
                
        else:
            print(f"\n❌ Error: {result.content}")
            print(f"   Errors: {result.errors}")
            
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "=" * 60)

async def test_memory_persistence():
    """Test that Letta remembers previous conversations"""
    
    print("\n🧠 Testing Letta Memory Persistence")
    print("=" * 60)
    
    try:
        # Create supervisor
        supervisor = GlobalSupervisorAgent(task_id="test_memory_001")
        
        # First task
        print("\n1️⃣ First interaction - introducing a concept...")
        task1 = Task(
            task_id="test_memory_001",
            task_type="analysis",
            description="Remember this: Our company is called QuantumCorp and we specialize in quantum encryption.",
            priority="medium"
        )
        
        result1 = await supervisor.process_task(task1)
        print(f"   Response: {result1.content}")
        
        # Second task - test memory
        print("\n2️⃣ Second interaction - testing memory...")
        task2 = Task(
            task_id="test_memory_002",
            task_type="question",
            description="What is the name of our company and what do we specialize in?",
            priority="medium"
        )
        
        # Use same supervisor instance to maintain memory
        result2 = await supervisor.process_task(task2)
        
        if result2.success:
            response = result2.content.get('deliverables', {}).get('analysis', '')
            if 'QuantumCorp' in response and 'quantum encryption' in response:
                print("   ✅ Memory test PASSED - Letta remembered the information!")
            else:
                print("   ⚠️ Memory test INCONCLUSIVE - Check response manually")
            print(f"   Response: {response[:200]}...")
        
    except Exception as e:
        print(f"\n❌ Memory test failed: {e}")

async def main():
    """Run all tests"""
    
    print("\n🚀 Letta Integration Test Suite")
    print("=" * 60)
    print("\nIMPORTANT: Make sure Letta server is running:")
    print("  letta server")
    print("  (Should be running on http://localhost:8283)")
    print("\nPress Ctrl+C to cancel if Letta is not running...")
    
    await asyncio.sleep(3)  # Give user time to cancel
    
    # Run tests
    await test_basic_letta_flow()
    # await test_memory_persistence()  # Uncomment when basic flow works
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())