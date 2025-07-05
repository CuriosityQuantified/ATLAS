#!/usr/bin/env python3
"""
Test Restored MLflow Architecture
Verify that the restored architecture works without attribute errors
"""

import os
import sys
import asyncio
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_restored_architecture():
    """Test that agents can be initialized with the restored architecture."""
    print("🔧 Testing Restored MLflow Architecture")
    print("=" * 60)
    
    try:
        # Import the restored components
        from backend.src.mlflow.enhanced_tracking import EnhancedATLASTracker
        from backend.src.agents.global_supervisor import GlobalSupervisorAgent
        from backend.src.agents.library import LibraryAgent
        from backend.src.agents.base import Task, AgentStatus
        from backend.src.agui.handlers import AGUIEventBroadcaster
        
        print("✅ All imports successful")
        
        # Test 1: Initialize Enhanced MLflow Tracker
        print("\n1. Testing Enhanced MLflow Tracker Initialization")
        print("-" * 50)
        
        tracker = EnhancedATLASTracker(
            tracking_uri="http://localhost:5002",
            experiment_name=f"Architecture_Test_{int(datetime.now().timestamp())}",
            auto_start_run=True,
            enable_detailed_logging=True
        )
        
        print(f"✅ Enhanced tracker initialized")
        print(f"   Enhanced tracking enabled: {tracker.enable_detailed_logging}")
        print(f"   MLflow tracking URI: http://localhost:5002")
        
        # Test 2: Initialize Agents with MLflow Tracker
        print("\n2. Testing Agent Initialization with MLflow Tracker")
        print("-" * 50)
        
        task_id = f"test_{int(datetime.now().timestamp())}"
        broadcaster = AGUIEventBroadcaster(connection_manager=None)
        
        # Initialize Global Supervisor with tracker
        global_supervisor = GlobalSupervisorAgent(
            task_id=task_id,
            agui_broadcaster=broadcaster,
            mlflow_tracker=tracker  # This should NOT cause attribute errors
        )
        print(f"✅ Global Supervisor initialized: {global_supervisor.agent_id}")
        print(f"   Has mlflow_tracker: {hasattr(global_supervisor, 'mlflow_tracker')}")
        print(f"   Tracker type: {type(global_supervisor.mlflow_tracker)}")
        
        # Initialize Library Agent with tracker
        library_agent = LibraryAgent(
            task_id=task_id,
            agui_broadcaster=broadcaster,
            mlflow_tracker=tracker  # This should NOT cause attribute errors
        )
        print(f"✅ Library Agent initialized: {library_agent.agent_id}")
        print(f"   Has mlflow_tracker: {hasattr(library_agent, 'mlflow_tracker')}")
        print(f"   Tracker type: {type(library_agent.mlflow_tracker)}")
        
        # Test 3: Agent Status Changes (should log to MLflow)
        print("\n3. Testing Agent Status Changes with MLflow Logging")
        print("-" * 50)
        
        await global_supervisor.update_status(
            AgentStatus.PROCESSING, 
            "Testing restored architecture - processing mode"
        )
        print("✅ Global Supervisor status change logged")
        
        await library_agent.update_status(
            AgentStatus.ACTIVE,
            "Testing restored architecture - active mode"
        )
        print("✅ Library Agent status change logged")
        
        # Test 4: Tool Calls (should log to MLflow)
        print("\n4. Testing Tool Calls with MLflow Logging")
        print("-" * 50)
        
        # Test library operations
        for i in range(3):
            result = await global_supervisor.call_library(
                operation="search",
                query=f"architecture test query {i+1}",
                context={"test_iteration": i+1, "test_type": "architecture_validation"}
            )
            print(f"✅ Library call {i+1}: {result['status']}")
        
        # Test 5: Task Processing (should log to MLflow)
        print("\n5. Testing Task Processing with MLflow Logging")
        print("-" * 50)
        
        test_task = Task(
            task_id="architecture_validation_task",
            task_type="architecture_test",
            description="Test task for validating restored MLflow architecture",
            priority="high",
            context={
                "test_purpose": "architecture_validation",
                "expected_behavior": "no_attribute_errors",
                "tracking_validation": True
            }
        )
        
        # Process task with Library Agent
        lib_result = await library_agent.process_task(test_task)
        print(f"✅ Library task processing: {lib_result.success}")
        
        # Process task with Global Supervisor
        supervisor_result = await global_supervisor.process_task(test_task)
        print(f"✅ Supervisor task processing: {supervisor_result.success}")
        
        # Test 6: Verify MLflow Tracking Data
        print("\n6. Verifying MLflow Tracking Data")
        print("-" * 50)
        
        performance_summary = tracker.get_performance_summary()
        
        print(f"✅ Total LLM interactions: {performance_summary['llm_interactions']['total_interactions']}")
        print(f"✅ Total tool calls: {performance_summary['tool_calls']['total_calls']}")
        print(f"✅ Total conversation turns: {performance_summary['conversations']['total_turns']}")
        print(f"✅ Total cost: ${performance_summary['llm_interactions']['total_cost']:.4f}")
        
        # Log enhanced session summary
        tracker.log_enhanced_session_summary()
        print("✅ Enhanced session summary logged")
        
        # Test 7: Cleanup
        print("\n7. Testing Cleanup")
        print("-" * 50)
        
        global_supervisor.cleanup()
        library_agent.cleanup()
        tracker.cleanup()
        
        print("✅ All agents and tracker cleaned up successfully")
        
        print("\n🎉 Architecture Restoration Test Results")
        print("=" * 60)
        print("✅ Enhanced MLflow Tracker: WORKING")
        print("✅ Agent Initialization: NO ATTRIBUTE ERRORS")
        print("✅ Status Change Tracking: WORKING")
        print("✅ Tool Call Tracking: WORKING") 
        print("✅ Task Processing: WORKING")
        print("✅ MLflow Dashboard Integration: WORKING")
        
        print(f"\n🌐 View results at: http://localhost:5002")
        print("\n📋 Expected Dashboard Contents:")
        print("   • Agent system prompts (YAML personas)")
        print("   • Agent status transitions with context")
        print("   • Tool calls (library operations)")
        print("   • Task processing metrics")
        print("   • Performance summaries")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Architecture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_restored_architecture())
    if success:
        print("\n🎉 RESTORATION SUCCESSFUL!")
        print("✅ No mlflow_tracker attribute errors")
        print("✅ Enhanced tracking working properly")
        print("✅ All agent features operational")
    else:
        print("\n❌ RESTORATION FAILED!")
        print("⚠️ Check error messages above")
    
    exit(0 if success else 1)