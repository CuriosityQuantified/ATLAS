#!/usr/bin/env python3
"""
Test script for ATLAS agent coordination between Global Supervisor and Library Agent
Demonstrates base functionality, coordination patterns, and AG-UI integration
"""

import os
import sys
import asyncio
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.src.agents.global_supervisor import GlobalSupervisorAgent
from backend.src.agents.library import LibraryAgent
from backend.src.agents.base import Task, TaskResult
from backend.src.agui.handlers import AGUIEventBroadcaster
from backend.src.mlflow.tracking import ATLASMLflowTracker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_library_operations():
    """Test basic Library Agent operations."""
    print("\n🔍 Testing Library Agent Operations")
    print("-" * 50)
    
    # Initialize Library Agent
    library = LibraryAgent(
        task_id="library_test_001",
        agui_broadcaster=AGUIEventBroadcaster(connection_manager=None),
        mlflow_tracker=ATLASMLflowTracker()
    )
    
    try:
        # Test 1: Add operation
        print("📚 Test 1: Adding knowledge to library")
        add_task = Task(
            task_id="add_test_001",
            task_type="library_add",
            description="Store test knowledge",
            context={
                "operation": "add",
                "data": {
                    "type": "test_pattern",
                    "content": "This is a test pattern for ATLAS coordination",
                    "category": "testing",
                    "tags": ["test", "coordination", "pattern"]
                },
                "context": {
                    "category": "patterns",
                    "requesting_agent": "test_script"
                }
            }
        )
        
        add_result = await library.process_task(add_task)
        print(f"✅ Add result: {add_result.success}")
        print(f"   Entry ID: {add_result.content.get('entry_id', 'N/A')}")
        
        # Test 2: Search operation
        print("\n🔎 Test 2: Searching library")
        search_task = Task(
            task_id="search_test_001",
            task_type="library_search",
            description="Search for test patterns",
            context={
                "operation": "search",
                "query": "test pattern coordination",
                "context": {
                    "search_type": "patterns",
                    "limit": 5,
                    "include_patterns": True
                }
            }
        )
        
        search_result = await library.process_task(search_task)
        print(f"✅ Search result: {search_result.success}")
        print(f"   Results found: {search_result.content.get('total_found', 0)}")
        
        # Test 3: Library stats
        print("\n📊 Test 3: Getting library statistics")
        stats_task = Task(
            task_id="stats_test_001",
            task_type="library_stats", 
            description="Get library statistics",
            context={
                "operation": "get_stats",
                "context": {}
            }
        )
        
        stats_result = await library.process_task(stats_task)
        print(f"✅ Stats result: {stats_result.success}")
        print(f"   Total entries: {stats_result.content.get('library_stats', {}).get('total_entries', 0)}")
        
        return library
        
    except Exception as e:
        print(f"❌ Library test failed: {e}")
        return None
    finally:
        library.cleanup()

async def test_global_supervisor():
    """Test Global Supervisor functionality."""
    print("\n🎯 Testing Global Supervisor")
    print("-" * 50)
    
    # Initialize Global Supervisor
    supervisor = GlobalSupervisorAgent(
        task_id="supervisor_test_001",
        agui_broadcaster=AGUIEventBroadcaster(connection_manager=None),
        mlflow_tracker=ATLASMLflowTracker()
    )
    
    try:
        # Test complex task processing
        print("🎯 Test: Processing complex task with Global Supervisor")
        complex_task = Task(
            task_id="complex_test_001",
            task_type="strategic_analysis",
            description="Analyze market trends and create strategic recommendations for AI adoption in enterprise software",
            priority="high",
            context={
                "industry": "enterprise_software",
                "focus_areas": ["AI adoption", "market trends", "strategic planning"],
                "deliverable_format": "comprehensive_report",
                "deadline": "2 hours"
            }
        )
        
        start_time = time.time()
        result = await supervisor.process_task(complex_task)
        processing_time = time.time() - start_time
        
        print(f"✅ Supervisor result: {result.success}")
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Teams involved: {result.metadata.get('teams_involved', 0)}")
        print(f"   Strategy used: {result.metadata.get('coordination_strategy', 'N/A')}")
        
        # Display result summary
        if result.success and isinstance(result.content, dict):
            task_summary = result.content.get("task_summary", {})
            print(f"   Completion status: {task_summary.get('completion_status', 'N/A')}")
            print(f"   Teams assigned: {task_summary.get('teams_involved', 0)}")
        
        return supervisor
        
    except Exception as e:
        print(f"❌ Global Supervisor test failed: {e}")
        return None
    finally:
        supervisor.cleanup()

async def test_coordination():
    """Test coordination between Global Supervisor and Library Agent."""
    print("\n🤝 Testing Agent Coordination")
    print("-" * 50)
    
    # Initialize both agents
    library = LibraryAgent(
        task_id="coordination_test",
        agui_broadcaster=AGUIEventBroadcaster(connection_manager=None),
        mlflow_tracker=ATLASMLflowTracker()
    )
    
    supervisor = GlobalSupervisorAgent(
        task_id="coordination_test",
        agui_broadcaster=AGUIEventBroadcaster(connection_manager=None),
        mlflow_tracker=ATLASMLflowTracker()
    )
    
    try:
        # Test 1: Global Supervisor calls Library Agent
        print("📞 Test: Global Supervisor calling Library Agent")
        
        # Supervisor searches library for relevant patterns
        library_response = await supervisor.call_library(
            operation="search",
            query="strategic analysis patterns",
            context={
                "search_type": "patterns",
                "requesting_context": "task_decomposition"
            }
        )
        
        print(f"✅ Library call result: {library_response.get('status', 'unknown')}")
        print(f"   Operation: {library_response.get('operation', 'N/A')}")
        
        # Test 2: Store coordination result in library
        coordination_data = {
            "type": "coordination_test",
            "supervisor_id": supervisor.agent_id,
            "library_id": library.agent_id,
            "test_timestamp": datetime.now().isoformat(),
            "coordination_success": True
        }
        
        store_response = await supervisor.call_library(
            operation="add",
            data=coordination_data,
            context={
                "category": "coordination_tests",
                "test_phase": "integration"
            }
        )
        
        print(f"✅ Store coordination result: {store_response.get('status', 'unknown')}")
        
        # Test 3: Verify agents can access each other's data
        verify_task = Task(
            task_id="verify_coordination",
            task_type="coordination_verification",
            description="Verify coordination data storage",
            context={
                "operation": "search",
                "query": "coordination_test",
                "context": {"search_type": "general"}
            }
        )
        
        verification_result = await library.process_task(verify_task)
        print(f"✅ Verification result: {verification_result.success}")
        if verification_result.success:
            results_count = verification_result.content.get("total_found", 0)
            print(f"   Coordination records found: {results_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Coordination test failed: {e}")
        return False
    finally:
        library.cleanup()
        supervisor.cleanup()

async def test_ag_ui_integration():
    """Test AG-UI event broadcasting integration."""
    print("\n📡 Testing AG-UI Integration")
    print("-" * 50)
    
    # Initialize with event broadcasting
    broadcaster = AGUIEventBroadcaster(connection_manager=None)
    
    library = LibraryAgent(
        task_id="agui_test",
        agui_broadcaster=broadcaster,
        mlflow_tracker=ATLASMLflowTracker()
    )
    
    supervisor = GlobalSupervisorAgent(
        task_id="agui_test",
        agui_broadcaster=broadcaster,
        mlflow_tracker=ATLASMLflowTracker()
    )
    
    try:
        print("📡 Testing agent status broadcasting")
        
        # Test status updates
        await library.update_status(library.status, "Testing AG-UI integration")
        await supervisor.update_status(supervisor.status, "Coordinating with Library Agent")
        
        print("✅ Status updates broadcasted successfully")
        
        # Test task processing with events
        simple_task = Task(
            task_id="agui_integration_test",
            task_type="simple_test",
            description="Test AG-UI event broadcasting during task processing"
        )
        
        # Process task and observe events
        result = await library.process_task(simple_task)
        print(f"✅ Task processed with AG-UI events: {result.success}")
        
        return True
        
    except Exception as e:
        print(f"❌ AG-UI integration test failed: {e}")
        return False
    finally:
        library.cleanup()
        supervisor.cleanup()

async def main():
    """Run comprehensive agent coordination tests."""
    print("🚀 ATLAS Agent Coordination Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Run individual tests
    library_result = await test_library_operations()
    test_results.append(("Library Operations", library_result is not None))
    
    supervisor_result = await test_global_supervisor()
    test_results.append(("Global Supervisor", supervisor_result is not None))
    
    coordination_result = await test_coordination()
    test_results.append(("Agent Coordination", coordination_result))
    
    agui_result = await test_ag_ui_integration()
    test_results.append(("AG-UI Integration", agui_result))
    
    # Print summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All agent coordination tests completed successfully!")
        print("✅ Ready to proceed with team supervisor implementation")
    else:
        print("⚠️  Some tests failed - review implementation before proceeding")
    
    return passed == total

if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    sys.exit(0 if success else 1)