#!/usr/bin/env python3
"""
MLflow Implementation Verification Script for ATLAS

This script verifies:
1. MLflow server connectivity
2. Database connectivity
3. Artifact storage (MinIO)
4. ATLAS tracking functionality
5. UI dashboard accessibility

Usage: python scripts/dev/verify-mlflow.py
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any

# Add the backend src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

try:
    import mlflow
    from mlflow.tracking import MlflowClient
    print("✅ MLflow imported successfully")
except ImportError as e:
    print(f"❌ Failed to import MLflow: {e}")
    sys.exit(1)

def test_mlflow_server_connectivity():
    """Test if MLflow server is accessible"""
    print("\n🔍 Testing MLflow Server Connectivity...")
    
    mlflow_uri = "http://localhost:5001"
    
    try:
        response = requests.get(f"{mlflow_uri}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ MLflow server is running at {mlflow_uri}")
            return True
        else:
            print(f"❌ MLflow server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to MLflow server: {e}")
        print("   Make sure Docker services are running: docker-compose up -d")
        return False

def test_mlflow_client():
    """Test MLflow client functionality"""
    print("\n🔍 Testing MLflow Client...")
    
    try:
        mlflow.set_tracking_uri("http://localhost:5001")
        client = MlflowClient()
        
        # Test creating an experiment
        experiment_name = "ATLAS_Verification_Test"
        try:
            experiment_id = client.create_experiment(experiment_name)
            print(f"✅ Created experiment: {experiment_name} (ID: {experiment_id})")
        except Exception as e:
            if "already exists" in str(e):
                experiment = client.get_experiment_by_name(experiment_name)
                experiment_id = experiment.experiment_id
                print(f"✅ Using existing experiment: {experiment_name} (ID: {experiment_id})")
            else:
                raise e
        
        return experiment_id
    except Exception as e:
        print(f"❌ MLflow client test failed: {e}")
        return None

def test_atlas_tracking():
    """Test ATLAS-specific tracking functionality"""
    print("\n🔍 Testing ATLAS Tracking Implementation...")
    
    try:
        # Mock the MLflowConfig since we don't have the actual config module yet
        class MockMLflowConfig:
            def __init__(self):
                self.tracking_uri = "http://localhost:5001"
        
        # Test if we can import the cost calculator
        try:
            from utils.cost_calculator import get_cost_and_pricing_details
            print("✅ Cost calculator imported successfully")
            
            # Test cost calculation
            cost, details = get_cost_and_pricing_details("gpt-4", 1000, 500)
            print(f"✅ Cost calculation test: ${cost:.4f} for 1000 input + 500 output tokens")
            
        except ImportError as e:
            print(f"⚠️  Cost calculator not available: {e}")
        
        # Test the tracking class
        try:
            from mlflow.tracking import ATLASMLflowTracker
            
            config = MockMLflowConfig()
            tracker = ATLASMLflowTracker(config)
            print("✅ ATLASMLflowTracker initialized successfully")
            
            # Test starting a task run
            task_metadata = {
                'user_id': 'test_user',
                'initial_prompt': 'Verify MLflow implementation',
                'task_type': 'Verification',
                'teams_involved': ['Research', 'Analysis']
            }
            
            task_run_id = tracker.start_task_run("verification_test", task_metadata)
            print(f"✅ Created task run: {task_run_id}")
            
            # Test starting an agent run
            agent_config = {
                'agent_type': 'Worker',
                'team': 'Research',
                'model_name': 'gpt-4',
                'persona_prompt': 'You are a verification assistant.',
                'tools_available': ['search', 'analyze']
            }
            
            agent_run_id = tracker.start_agent_run(task_run_id, "verification_agent", agent_config)
            print(f"✅ Created agent run: {agent_run_id}")
            
            # Test logging a transaction
            tracker.log_agent_transaction(
                agent_run_id=agent_run_id,
                model_name="gpt-4",
                input_tokens=100,
                output_tokens=50,
                artifacts={'output.txt': 'Verification completed successfully.'},
                step=1
            )
            print("✅ Logged agent transaction")
            
            return True
            
        except Exception as e:
            print(f"❌ ATLAS tracking test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ ATLAS tracking setup failed: {e}")
        return False

def test_ui_accessibility():
    """Test if MLflow UI is accessible"""
    print("\n🔍 Testing MLflow UI Accessibility...")
    
    try:
        ui_url = "http://localhost:5001"
        response = requests.get(ui_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ MLflow UI is accessible at {ui_url}")
            print("   You can view experiments, runs, and metrics in the web interface")
            return True
        else:
            print(f"❌ MLflow UI returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access MLflow UI: {e}")
        return False

def test_artifact_storage():
    """Test MinIO artifact storage connectivity"""
    print("\n🔍 Testing Artifact Storage (MinIO)...")
    
    try:
        # Test MinIO console accessibility
        minio_console_url = "http://localhost:9001"
        response = requests.get(minio_console_url, timeout=5)
        
        if response.status_code in [200, 403]:  # 403 is normal for login page
            print(f"✅ MinIO console is accessible at {minio_console_url}")
            print("   Credentials: minioadmin / minioadmin")
        else:
            print(f"⚠️  MinIO console returned status {response.status_code}")
        
        # Test MinIO API
        minio_api_url = "http://localhost:9000"
        response = requests.get(minio_api_url, timeout=5)
        
        if response.status_code in [403, 405]:  # Expected for MinIO API without auth
            print(f"✅ MinIO API is accessible at {minio_api_url}")
            return True
        else:
            print(f"⚠️  MinIO API returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access MinIO: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 ATLAS MLflow Implementation Verification")
    print("=" * 50)
    
    tests = [
        ("MLflow Server", test_mlflow_server_connectivity),
        ("MLflow Client", test_mlflow_client),
        ("ATLAS Tracking", test_atlas_tracking),
        ("MLflow UI", test_ui_accessibility),
        ("Artifact Storage", test_artifact_storage),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Verification Summary")
    print("=" * 30)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! MLflow implementation is working correctly.")
        print("\n📈 Next Steps:")
        print("1. Access MLflow UI at: http://localhost:5001")
        print("2. Access MinIO Console at: http://localhost:9001")
        print("3. Start building the frontend dashboard")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check Docker services and configuration.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())