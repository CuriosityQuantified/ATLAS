#!/usr/bin/env python3
"""
Test Frontend-Backend Agent Communication with MLflow Tracking
Simulates the frontend creating agent tasks and verifies MLflow tracking
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_frontend_backend_mlflow():
    """Test frontend-backend communication with MLflow tracking verification."""
    print("🚀 Frontend-Backend MLflow Integration Test")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Create Agent Task (should create MLflow run)
        print("\n1. Creating Agent Task via API")
        print("-" * 50)
        
        task_request = {
            "task_type": "strategic_analysis",
            "description": "Test task for MLflow dashboard verification - analyze market trends",
            "priority": "high",
            "context": {
                "industry": "technology",
                "focus_areas": ["market_trends", "competitive_analysis"],
                "deliverable_format": "strategic_report"
            }
        }
        
        try:
            create_response = await client.post(
                f"{base_url}/api/agents/tasks",
                json=task_request
            )
            
            if create_response.status_code == 200:
                task_data = create_response.json()
                task_id = task_data["task_id"]
                mlflow_run_id = task_data.get("mlflow_run_id")
                mlflow_url = task_data.get("mlflow_url")
                
                print(f"✅ Task created: {task_id}")
                print(f"✅ MLflow run ID: {mlflow_run_id}")
                print(f"🌐 MLflow URL: {mlflow_url}")
                
                # Test 2: Start Task Processing
                print(f"\n2. Starting Task Processing")
                print("-" * 50)
                
                start_response = await client.post(
                    f"{base_url}/api/agents/tasks/{task_id}/start"
                )
                
                if start_response.status_code == 200:
                    start_data = start_response.json()
                    print(f"✅ Task started: {start_data['status']}")
                    
                    # Wait for some processing
                    await asyncio.sleep(2)
                    
                    # Test 3: Check Task Status
                    print(f"\n3. Checking Task Status")
                    print("-" * 50)
                    
                    status_response = await client.get(
                        f"{base_url}/api/agents/tasks/{task_id}/status"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"✅ Task status: {status_data['status']}")
                        print(f"   Progress: {status_data['progress']}%")
                        print(f"   Current phase: {status_data['current_phase']}")
                        print(f"   Agents active: {status_data['agents_active']}")
                    
                    # Test 4: Send User Input (should generate more tracking)
                    print(f"\n4. Sending User Input")
                    print("-" * 50)
                    
                    user_input = {
                        "message": "Please focus on emerging AI technologies and their market impact",
                        "agent_id": "global_supervisor",
                        "context": {
                            "input_type": "guidance",
                            "priority": "high"
                        }
                    }
                    
                    input_response = await client.post(
                        f"{base_url}/api/agents/tasks/{task_id}/input",
                        json=user_input
                    )
                    
                    if input_response.status_code == 200:
                        input_data = input_response.json()
                        print(f"✅ User input sent: {input_data['status']}")
                        print(f"   Forwarded to: {input_data['agent_id']}")
                    
                    # Test 5: Get Agent Information
                    print(f"\n5. Getting Agent Information")
                    print("-" * 50)
                    
                    agents_response = await client.get(
                        f"{base_url}/api/agents/tasks/{task_id}/agents"
                    )
                    
                    if agents_response.status_code == 200:
                        agents_data = agents_response.json()
                        print(f"✅ Total agents: {agents_data['total_agents']}")
                        
                        for agent_key, agent_info in agents_data['agents'].items():
                            print(f"   {agent_key}: {agent_info['status']} ({agent_info['agent_type']})")
                    
                    # Test 6: Library Operations
                    print(f"\n6. Testing Library Operations")
                    print("-" * 50)
                    
                    library_ops = [
                        {
                            "operation": "search",
                            "query": "strategic analysis patterns",
                            "context": {"search_type": "patterns"}
                        },
                        {
                            "operation": "add",
                            "data": {
                                "type": "test_pattern",
                                "content": "Frontend-backend MLflow integration test",
                                "category": "testing"
                            },
                            "context": {"category": "integration_tests"}
                        }
                    ]
                    
                    for i, lib_op in enumerate(library_ops):
                        lib_response = await client.post(
                            f"{base_url}/api/agents/library/operation",
                            json=lib_op
                        )
                        
                        if lib_response.status_code == 200:
                            lib_data = lib_response.json()
                            print(f"✅ Library operation {i+1}: {lib_data['success']}")
                            print(f"   Operation: {lib_data['operation']}")
                    
                    # Final status check
                    await asyncio.sleep(1)
                    
                    final_status_response = await client.get(
                        f"{base_url}/api/agents/tasks/{task_id}/status"
                    )
                    
                    if final_status_response.status_code == 200:
                        final_status = final_status_response.json()
                        print(f"\n📊 Final Task Status")
                        print("-" * 50)
                        print(f"Status: {final_status['status']}")
                        print(f"Progress: {final_status['progress']}%")
                        print(f"Phase: {final_status['current_phase']}")
                    
                    print(f"\n🎯 MLflow Dashboard Verification")
                    print("=" * 60)
                    print(f"📊 Experiment ID: {task_data.get('mlflow_run_id', 'N/A')}")
                    print(f"🌐 MLflow URL: {mlflow_url}")
                    print(f"📈 Expected metrics in dashboard:")
                    print(f"   • Task creation parameters")
                    print(f"   • Agent state changes")
                    print(f"   • Tool calls (library operations)")
                    print(f"   • User input events")
                    print(f"   • Agent coordination metrics")
                    print(f"   • Task processing metrics")
                    
                    return True
                    
                else:
                    print(f"❌ Failed to start task: {start_response.status_code}")
                    return False
            else:
                print(f"❌ Failed to create task: {create_response.status_code}")
                print(f"Response: {create_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during frontend-backend test: {e}")
            return False

async def check_backend_status():
    """Check if backend is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/")
            return response.status_code == 200
    except:
        return False

async def main():
    """Run the frontend-backend MLflow integration test."""
    print("🔍 Checking backend status...")
    
    if not await check_backend_status():
        print("❌ Backend not running. Please start with: uvicorn main:app --reload")
        return False
    
    print("✅ Backend is running")
    
    success = await test_frontend_backend_mlflow()
    
    if success:
        print("\n🎉 Frontend-Backend MLflow Integration Test Completed Successfully!")
        print("👀 Please check the MLflow dashboard to verify all metrics are visible")
        print("🌐 MLflow Dashboard: http://localhost:5002")
    else:
        print("\n❌ Test failed - check backend logs for details")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)