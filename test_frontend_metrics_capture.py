#!/usr/bin/env python3
"""
Test script to verify that frontend chat interactions capture metrics in MLflow
"""

import asyncio
import httpx
import time
import json

async def test_frontend_metrics_capture():
    """Test that frontend chat interactions properly capture metrics."""
    print("🧪 Testing Frontend Chat Metrics Capture")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Create a new task
            print("📝 Creating new task...")
            task_response = await client.post(f"{base_url}/api/tasks", json={
                "task_type": "chat_test",
                "description": "Test task for metrics capture verification",
                "priority": "high",
                "context": {"test_type": "metrics_verification"}
            })
            
            if task_response.status_code != 200:
                print(f"❌ Failed to create task: {task_response.status_code}")
                print(task_response.text)
                return
            
            task_data = task_response.json()
            task_id = task_data["task_id"]
            mlflow_run_id = task_data.get("mlflow_run_id")
            
            print(f"✅ Task created: {task_id}")
            print(f"🔬 MLflow run ID: {mlflow_run_id}")
            
            # 2. Start the task
            print("🚀 Starting task...")
            start_response = await client.post(f"{base_url}/api/tasks/{task_id}/start")
            
            if start_response.status_code != 200:
                print(f"❌ Failed to start task: {start_response.status_code}")
                return
            
            print("✅ Task started")
            
            # 3. Send user input (this should trigger LLM call and metrics)
            print("💬 Sending user input...")
            input_response = await client.post(f"{base_url}/api/tasks/{task_id}/input", json={
                "message": "Hello, can you help me understand how ATLAS works?",
                "agent_id": "global_supervisor",
                "context": {"test_message": True}
            })
            
            if input_response.status_code != 200:
                print(f"❌ Failed to send input: {input_response.status_code}")
                print(input_response.text)
                return
            
            input_data = input_response.json()
            print(f"✅ Input processed: {input_data['status']}")
            
            if input_data['status'] == 'processed':
                print(f"🤖 Agent response preview: {input_data.get('response', 'No response')}")
            
            # 4. Wait a moment for metrics to be logged
            print("⏳ Waiting for metrics to be logged...")
            await asyncio.sleep(3)
            
            # 5. Check task status
            print("📊 Checking final task status...")
            status_response = await client.get(f"{base_url}/api/tasks/{task_id}/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ Task status: {status_data['status']}")
                print(f"📈 Progress: {status_data['progress']}%")
                print(f"🔄 Current phase: {status_data['current_phase']}")
            
            print(f"\n🎯 Check MLflow dashboard at http://localhost:5002")
            print(f"🔍 Look for run ID: {mlflow_run_id}")
            print(f"📊 Expected metrics: LLM interactions, conversation turns, tool calls")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_frontend_metrics_capture())