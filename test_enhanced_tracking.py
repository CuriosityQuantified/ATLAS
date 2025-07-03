#!/usr/bin/env python3
"""
Test Enhanced MLflow Tracking
Quick test to verify comprehensive tracking is working
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/Users/nicholaspate/Documents/ATLAS/backend')

from src.agents.global_supervisor import GlobalSupervisorAgent
from src.agents.library import LibraryAgent
from src.agents.base import Task
from src.agui.handlers import AGUIEventBroadcaster
from src.mlflow.enhanced_tracking import EnhancedATLASTracker

async def test_enhanced_tracking():
    """Test enhanced tracking with a simple agent task."""
    print("🚀 Testing Enhanced MLflow Tracking")
    
    # Initialize enhanced tracker
    tracker = EnhancedATLASTracker()
    broadcaster = AGUIEventBroadcaster()
    
    # Start a task run
    task_id = "test_enhanced_tracking_001"
    task_metadata = {
        "task_type": "tracking_test",
        "description": "Test enhanced MLflow tracking capabilities",
        "priority": "high",
        "user_id": "test_user",
        "context": {"test": True, "purpose": "tracking_validation"}
    }
    
    print(f"📊 Starting task run: {task_id}")
    run_id = tracker.start_task_run(task_id, task_metadata)
    print(f"   Task run ID: {run_id}")
    
    # Start agent run
    agent_run_id = tracker.start_agent_run(
        agent_id="global_supervisor_test",
        agent_type="Global Supervisor",
        task_id=task_id
    )
    print(f"   Agent run ID: {agent_run_id}")
    
    # Test system prompt logging
    system_prompt = "You are a test Global Supervisor agent. Your role is to coordinate tasks efficiently."
    tracker.log_system_prompt("global_supervisor_test", system_prompt)
    print("✅ Logged system prompt")
    
    # Test user input logging
    user_input = "Please analyze the current state of our test system"
    tracker.log_user_input(user_input, "global_supervisor_test", {"request_type": "analysis"})
    print("✅ Logged user input")
    
    # Test tool call logging
    tracker.log_tool_call(
        tool_name="library_search",
        tool_type="library",
        input_params={"query": "test system state", "limit": 5},
        output_result={"results": [], "total_found": 0},
        agent_id="global_supervisor_test",
        success=True,
        processing_time_ms=150.0
    )
    print("✅ Logged tool call")
    
    # Test LLM interaction logging
    tracker.log_llm_interaction(
        model_name="claude-3-5-haiku-20241022",
        provider="anthropic",
        system_prompt=system_prompt,
        user_prompt=user_input,
        response="Based on the test system analysis, everything appears to be functioning correctly.",
        agent_id="global_supervisor_test",
        input_tokens=150,
        output_tokens=75,
        cost_usd=0.002,
        latency_ms=800.0,
        temperature=0.3
    )
    print("✅ Logged LLM interaction")
    
    # Test agent message logging
    tracker.log_agent_message(
        from_agent="global_supervisor_test",
        to_agent="research_team_supervisor",
        message_type="delegation",
        content={"task": "research_delegation", "priority": "medium"},
        message_id="msg_001"
    )
    print("✅ Logged agent message")
    
    # Test agent state change logging
    tracker.log_agent_state_change(
        agent_id="global_supervisor_test",
        old_state="idle",
        new_state="processing",
        reason="Started task processing",
        context={"task_id": task_id}
    )
    print("✅ Logged agent state change")
    
    # Test multi-modal content logging
    tracker.log_multi_modal_content(
        agent_id="global_supervisor_test",
        content_type="text",
        content_size=1024,
        processing_time_ms=50.0,
        metadata={"format": "markdown", "language": "en"}
    )
    print("✅ Logged multi-modal content")
    
    # End runs with summary
    tracker.end_agent_run("global_supervisor_test", {
        "final_status": "completed",
        "tasks_processed": 1,
        "success_rate": 1.0
    })
    print("✅ Ended agent run")
    
    tracker.end_task_run(task_id, {
        "task_status": "completed",
        "total_agents": 1,
        "completion_time": 5.0
    })
    print("✅ Ended task run")
    
    print("\n🎉 Enhanced tracking test completed successfully!")
    print(f"📈 Check MLflow UI at http://localhost:5002 for experiment: ATLAS_Task_{task_id}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_tracking())