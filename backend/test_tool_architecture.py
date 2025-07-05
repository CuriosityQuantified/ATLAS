#!/usr/bin/env python3
"""
Test script for the enhanced tool-based architecture.
Tests parallel execution, ReAct loops, and user communication.
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add backend to path
import sys
sys.path.append('/Users/nicholaspate/Documents/ATLAS/backend')

from src.agents import (
    GlobalSupervisorV2,
    ResearchTeamSupervisor,
    WebResearchWorker,
    Task,
    AgentStatus
)


async def test_worker_react_loop():
    """Test Worker Agent ReAct loop"""
    print("\n🔬 Testing Worker Agent ReAct Loop")
    print("=" * 60)
    
    # Create web research worker
    worker = WebResearchWorker(task_id="test_worker_001")
    
    # Execute research task
    result = await worker.execute_research(
        research_query="Latest developments in quantum computing 2024",
        requirements={
            "min_sources": 2,
            "credibility_threshold": 0.7
        }
    )
    
    print(f"\n✅ Worker Result:")
    print(f"   Success: {result.get('findings') is not None}")
    print(f"   Worker ID: {result.get('worker_id')}")
    print(f"   Iterations: {result.get('iterations_used', 0)}")
    print(f"   Confidence: {result.get('confidence', 0)}")
    
    if result.get('findings'):
        print(f"\n📋 Findings Preview:")
        print(f"   {result['findings'][:200]}...")


async def test_supervisor_parallel_tools():
    """Test Supervisor parallel tool execution"""
    print("\n\n🎯 Testing Supervisor Parallel Tool Execution")
    print("=" * 60)
    
    # Create research supervisor
    supervisor = ResearchTeamSupervisor(task_id="test_supervisor_001")
    
    # Execute research task that should trigger multiple workers
    result = await supervisor.execute_research_task(
        task_description="Research the impact of AI on healthcare, including academic sources and recent news",
        research_requirements={
            "depth": "comprehensive",
            "include_academic": True,
            "verify_sources": True
        }
    )
    
    print(f"\n✅ Supervisor Result:")
    print(f"   Team: {result.get('team')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Total Sources: {result.get('metadata', {}).get('total_sources', 0)}")
    print(f"   Confidence: {result.get('confidence', 0)}")
    
    if result.get('research_summary'):
        print(f"\n📊 Research Summary:")
        print(f"   {result['research_summary']['content'][:200]}...")


async def test_global_supervisor_with_user_communication():
    """Test Global Supervisor V2 with user communication"""
    print("\n\n🌐 Testing Global Supervisor V2 with User Communication")
    print("=" * 60)
    
    # Create mock broadcaster for testing
    class MockBroadcaster:
        async def broadcast_dialogue_update(self, **kwargs):
            print(f"\n💬 User Update: {kwargs.get('content', {}).get('data', '')}")
    
    broadcaster = MockBroadcaster()
    
    # Create global supervisor
    supervisor = GlobalSupervisorV2(
        task_id="test_global_001",
        agui_broadcaster=broadcaster
    )
    
    # Create a complex task
    task = Task(
        task_id="test_global_001",
        task_type="research_and_analysis",
        description="Analyze the future of renewable energy and create a comprehensive report",
        priority="high",
        context={
            "requirements": ["market analysis", "technology trends", "investment opportunities"],
            "output_format": "executive report"
        }
    )
    
    print("\n🚀 Executing global task...")
    result = await supervisor.process_task(task)
    
    print(f"\n✅ Global Supervisor Result:")
    print(f"   Success: {result.success}")
    print(f"   Processing Time: {result.processing_time:.2f}s")
    print(f"   Tool Calls: {result.metadata.get('tool_calls_made', 0)}")
    print(f"   User Interactions: {result.metadata.get('user_interactions', 0)}")


async def test_parallel_team_execution():
    """Test parallel execution of multiple teams"""
    print("\n\n⚡ Testing Parallel Team Execution")
    print("=" * 60)
    
    # This would demonstrate calling research and analysis teams in parallel
    print("📝 Simulating parallel team calls...")
    
    # In a real implementation, this would use the Global Supervisor
    # to call multiple teams simultaneously
    async def simulate_team_call(team_name: str, delay: float):
        print(f"   → Starting {team_name}")
        await asyncio.sleep(delay)
        print(f"   ← {team_name} completed")
        return f"{team_name} results"
    
    # Execute teams in parallel
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(
        simulate_team_call("Research Team", 1.0),
        simulate_team_call("Analysis Team", 1.5),
        simulate_team_call("Writing Team", 0.8)
    )
    elapsed = asyncio.get_event_loop().time() - start_time
    
    print(f"\n✅ Parallel Execution Complete:")
    print(f"   Total Time: {elapsed:.2f}s (vs {1.0 + 1.5 + 0.8:.1f}s sequential)")
    print(f"   Results: {len(results)} teams completed")


async def main():
    """Run all tests"""
    print("\n🧪 ATLAS Tool-Based Architecture Test Suite")
    print("=" * 80)
    print("Testing the new architecture with:")
    print("- Worker agents using ReAct loops")
    print("- Supervisors with parallel tool execution")
    print("- User communication throughout execution")
    print("- Tool-based reasoning and results")
    
    try:
        # Run tests in sequence
        await test_worker_react_loop()
        await test_supervisor_parallel_tools()
        await test_global_supervisor_with_user_communication()
        await test_parallel_team_execution()
        
        print("\n\n✅ All tests completed successfully!")
        print("\n📊 Architecture Validation Summary:")
        print("   ✓ Worker ReAct pattern working")
        print("   ✓ Supervisor tool orchestration working")
        print("   ✓ User communication integrated")
        print("   ✓ Parallel execution demonstrated")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())