#!/usr/bin/env python3
"""
End-to-end test for MLflow integration with ATLAS agents.
Tests agent tracking, tool monitoring, cost tracking, and dashboard generation.
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from src.agents.supervisor import Supervisor
from src.mlflow.agent_tracking import AgentMLflowTracker
from src.mlflow.cost_tracking import OpenAICostTracker
from src.mlflow.dashboards import ATLASDashboards
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


def test_agent_tracking():
    """Test agent creation and tool tracking."""
    print("\n=== Testing Agent Tracking ===\n")

    tracker = AgentMLflowTracker("ATLAS_Test")

    # Track agent creation
    tracker.track_agent_creation(
        agent_id="test_supervisor_1",
        agent_type="supervisor",
        tools=["plan_task", "create_todo", "delegate_research", "save_output"],
        model_config={"model": "gpt-4o", "temperature": 0.7}
    )
    print("✓ Agent creation tracked")

    # Track tool invocations
    tracker.track_tool_invocation(
        agent_id="test_supervisor_1",
        tool_name="plan_task",
        parameters={"task": "Research AI trends", "context": {}},
        result={"subtasks": ["search", "analyze", "summarize"]},
        success=True,
        duration_ms=1500
    )
    print("✓ Tool invocation tracked")

    # Track planning output
    tracker.track_planning_output(
        plan_id="plan_001",
        agent_id="test_supervisor_1",
        task="Research AI trends",
        subtasks=[
            {"id": "1", "description": "Search for sources"},
            {"id": "2", "description": "Analyze findings"},
            {"id": "3", "description": "Write summary"}
        ],
        dependencies={"2": ["1"], "3": ["2"]},
        duration_ms=1500
    )
    print("✓ Planning output tracked")

    # Track knowledge operation
    tracker.track_knowledge_operation(
        operation_type="store",
        agent_id="test_supervisor_1",
        knowledge_type="research",
        content_size=4096,
        success=True,
        duration_ms=250
    )
    print("✓ Knowledge operation tracked")

    # Get summary
    summary = tracker.get_comprehensive_session_summary()
    print(f"\n✓ Session Summary:")
    print(f"  - Agents created: {summary['agents_created']}")
    print(f"  - Tool usage: {summary['tool_usage']['total_tool_calls']} calls")
    print(f"  - Plans created: {summary['planning_metrics']['plans_created']}")
    print(f"  - Knowledge operations: {summary['knowledge_operations']['total_operations']}")

    tracker.close()
    return True


def test_cost_tracking():
    """Test OpenAI API cost tracking."""
    print("\n=== Testing Cost Tracking ===\n")

    cost_tracker = OpenAICostTracker()

    # Track GPT-4o call (supervisor/writing)
    cost = cost_tracker.track_api_call(
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500,
        agent_id="supervisor_1",
        task_id="task_001",
        tool_name="plan_task"
    )
    print(f"✓ GPT-4o call tracked: ${cost:.4f}")

    # Track GPT-4o-mini call (research/analysis)
    cost = cost_tracker.track_api_call(
        model="gpt-4o-mini",
        input_tokens=800,
        output_tokens=300,
        agent_id="research_1",
        task_id="task_001",
        tool_name="delegate_research"
    )
    print(f"✓ GPT-4o-mini call tracked: ${cost:.4f}")

    # Track embedding call
    cost = cost_tracker.track_api_call(
        model="text-embedding-3-small",
        input_tokens=500,
        output_tokens=0,
        agent_id="supervisor_1",
        task_id="task_001",
        tool_name=None
    )
    print(f"✓ Embedding call tracked: ${cost:.6f}")

    # Get cost summary
    summary = cost_tracker.get_cost_summary()
    print(f"\n✓ Cost Summary:")
    print(f"  - Total cost: ${summary['total_cost_usd']:.4f}")
    print(f"  - Total tokens: {summary['total_tokens']:,}")
    print(f"  - Average per call: ${summary['avg_cost_per_call']:.4f}")
    print(f"  - Cost by model:")
    for model, cost in summary['cost_by_model'].items():
        print(f"    - {model}: ${cost:.4f}")

    # Check efficiency
    efficiency = cost_tracker.get_token_efficiency_metrics()
    print(f"\n✓ Token Efficiency:")
    print(f"  - Tokens per dollar: {efficiency['tokens_per_dollar']:,}")
    print(f"  - Input/Output ratio: {efficiency['input_output_ratio']:.2f}")

    # Generate report
    report = cost_tracker.export_cost_report()
    print("\n✓ Cost report generated")

    return True


def test_dashboards():
    """Test dashboard generation and reporting."""
    print("\n=== Testing Dashboard Generation ===\n")

    dashboards = ATLASDashboards()

    # Note: These tests would normally query real MLflow data
    # For now, we're testing the structure and methods
    print("✓ Dashboard manager initialized")

    # Test report generation (will show empty data without real runs)
    report = dashboards.generate_dashboard_report("ATLAS_Test", time_window_hours=1)
    print("✓ Dashboard report generated")

    # Show report structure
    print("\nReport Preview (first 500 chars):")
    print(report[:500])

    return True


def test_supervisor_with_mlflow():
    """Test supervisor agent with MLflow integration."""
    print("\n=== Testing Supervisor with MLflow ===\n")

    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found, skipping supervisor test")
        return False

    try:
        # Create supervisor with MLflow tracking
        task_id = f"test_{datetime.now().strftime('%H%M%S')}"
        mlflow_tracker = AgentMLflowTracker(f"ATLAS_Task_{task_id}")

        print("Creating supervisor agent with MLflow tracking...")
        supervisor = Supervisor(task_id, mlflow_tracker)
        print(f"✓ Supervisor created: {supervisor.agent.id}")

        # Get status
        status = supervisor.get_status()
        print(f"✓ Supervisor status retrieved:")
        print(f"  - Agent ID: {status['agent_id']}")
        print(f"  - Tools available: {len(status['tools_available'])}")

        # Send test message (would make real API calls)
        print("\n Sending test message...")
        response = supervisor.send_message("Create a plan for testing MLflow integration")
        print(f"✓ Message processed, response received")

        # Clean up
        supervisor.cleanup()
        print("✓ Supervisor cleaned up successfully")

        return True

    except Exception as e:
        print(f"✗ Error testing supervisor: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_workflow():
    """Test a complete workflow with all tracking components."""
    print("\n=== Testing Integrated Workflow ===\n")

    # Initialize all trackers
    mlflow_tracker = AgentMLflowTracker("ATLAS_Integration_Test")
    cost_tracker = OpenAICostTracker()

    print("✓ All trackers initialized")

    # Simulate agent workflow
    agent_id = "test_agent_workflow"

    # 1. Agent creation
    mlflow_tracker.track_agent_creation(
        agent_id=agent_id,
        agent_type="supervisor",
        tools=["plan_task", "delegate_research", "save_output"],
        model_config={"model": "gpt-4o"}
    )

    # 2. Planning
    start_time = time.time()
    mlflow_tracker.track_planning_output(
        plan_id="workflow_plan_1",
        agent_id=agent_id,
        task="Complete integration test",
        subtasks=[
            {"id": "1", "description": "Initialize trackers"},
            {"id": "2", "description": "Execute workflow"},
            {"id": "3", "description": "Generate reports"}
        ],
        dependencies={"2": ["1"], "3": ["2"]},
        duration_ms=(time.time() - start_time) * 1000
    )

    # 3. Tool execution with cost tracking
    cost = cost_tracker.track_api_call(
        model="gpt-4o",
        input_tokens=1200,
        output_tokens=600,
        agent_id=agent_id,
        task_id="integration_test",
        tool_name="plan_task"
    )

    mlflow_tracker.track_tool_invocation(
        agent_id=agent_id,
        tool_name="plan_task",
        parameters={"task": "Integration test"},
        result={"success": True},
        success=True,
        duration_ms=1800
    )

    # 4. Knowledge storage
    mlflow_tracker.track_knowledge_operation(
        operation_type="store",
        agent_id=agent_id,
        knowledge_type="test_results",
        content_size=2048,
        success=True,
        duration_ms=150
    )

    # 5. Generate summaries
    mlflow_summary = mlflow_tracker.get_comprehensive_session_summary()
    cost_summary = cost_tracker.get_cost_summary()

    print("\n✓ Integrated Workflow Results:")
    print(f"  - Total tool calls: {mlflow_summary['tool_usage']['total_tool_calls']}")
    print(f"  - Plans created: {mlflow_summary['planning_metrics']['plans_created']}")
    print(f"  - Total cost: ${cost_summary['total_cost_usd']:.4f}")
    print(f"  - Tokens used: {cost_summary['total_tokens']:,}")

    # Close tracking
    mlflow_tracker.close()

    print("\n✓ Integrated workflow completed successfully")

    return True


def main():
    """Run all MLflow integration tests."""
    print("\n" + "="*60)
    print("  ATLAS MLflow Integration Tests")
    print("="*60)

    # Track results
    results = []

    # Test 1: Agent tracking
    results.append(("Agent Tracking", test_agent_tracking()))

    # Test 2: Cost tracking
    results.append(("Cost Tracking", test_cost_tracking()))

    # Test 3: Dashboard generation
    results.append(("Dashboard Generation", test_dashboards()))

    # Test 4: Supervisor with MLflow
    results.append(("Supervisor with MLflow", test_supervisor_with_mlflow()))

    # Test 5: Integrated workflow
    results.append(("Integrated Workflow", test_integrated_workflow()))

    # Summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:30} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All MLflow integration tests passed!")
        print("\nPhase 3 (MLflow Integration) is now complete.")
        print("\nNext steps:")
        print("1. Begin Phase 4: Tool Implementation (Firecrawl, E2B)")
        print("2. Monitor MLflow dashboard at http://localhost:5002")
        print("3. Review cost tracking reports for optimization")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")

    return passed == total


if __name__ == "__main__":
    # Run the tests
    success = main()
    sys.exit(0 if success else 1)