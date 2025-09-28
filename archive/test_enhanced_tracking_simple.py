#!/usr/bin/env python3
"""
Simple test for Enhanced MLflow Tracking System
Tests core functionality with existing methods
"""

import sys
import os
import asyncio
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.src.mlflow.enhanced_tracking import EnhancedATLASTracker

async def test_enhanced_tracking_simple():
    """Test enhanced MLflow tracking with available methods."""
    print("🚀 Testing Enhanced MLflow Tracking (Simple)")
    print("-" * 60)
    
    try:
        # Initialize enhanced tracker
        tracker = EnhancedATLASTracker()
        print("✅ Enhanced tracker initialized")
        
        # Test LLM interaction logging
        interaction_id = f"test_interaction_{int(time.time())}"
        print(f"\n📝 Testing LLM interaction logging (ID: {interaction_id})")
        
        # Log an LLM interaction
        tracker.log_llm_interaction(
            interaction_id=interaction_id,
            agent_id="test_agent",
            model_name="claude-3-5-haiku-20241022",
            provider="anthropic",
            system_prompt="You are a test assistant.",
            user_prompt="What is the current time?",
            response=f"The current time is {datetime.now().isoformat()}",
            input_tokens=25,
            output_tokens=42,
            cost_usd=0.001,
            latency_ms=850.5,
            success=True,
            temperature=0.7,
            max_tokens=1000
        )
        print("✅ LLM interaction logged successfully")
        
        # Test tool call logging
        tool_call_id = f"test_tool_{int(time.time())}"
        print(f"\n🔧 Testing tool call logging (ID: {tool_call_id})")
        
        tracker.log_tool_call(
            tool_call_id=tool_call_id,
            agent_id="test_agent",
            tool_name="library_search",
            input_data={"query": "test search", "filters": ["type:document"]},
            output_data={"results": [{"title": "Test Document", "relevance": 0.95}]},
            execution_time_ms=250.0,
            success=True,
            metadata={"search_type": "semantic", "result_count": 1}
        )
        print("✅ Tool call logged successfully")
        
        # Test conversation turn logging
        turn_id = f"test_turn_{int(time.time())}"
        print(f"\n💬 Testing conversation turn logging (ID: {turn_id})")
        
        tracker.log_conversation_turn(
            turn_id=turn_id,
            agent_id="test_agent",
            user_message="Test user message",
            agent_response="Test agent response",
            turn_number=1,
            context={"task_type": "testing", "priority": "high"},
            response_time_ms=1200.0,
            user_satisfaction=None,
            metadata={"message_type": "text", "response_type": "text"}
        )
        print("✅ Conversation turn logged successfully")
        
        # Test performance summary
        print(f"\n📊 Testing performance summary")
        summary = tracker.get_performance_summary()
        print(f"✅ Performance summary generated: {len(summary)} metrics")
        for key, value in summary.items():
            print(f"   📈 {key}: {value}")
        
        # Test session summary
        print(f"\n🏁 Testing session summary logging")
        tracker.log_enhanced_session_summary()
        print("✅ Session summary logged successfully")
        
        print(f"\n🎉 All Enhanced MLflow Tracking tests passed!")
        print(f"🌐 View MLflow dashboard at: http://localhost:5002")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_tracking_simple())
    if not success:
        exit(1)