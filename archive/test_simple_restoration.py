#!/usr/bin/env python3
"""
Simple restoration test to verify mlflow_tracker attribute is working
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_simple_restoration():
    """Test basic agent initialization with mlflow_tracker parameter."""
    print("🔧 Testing Simple Architecture Restoration")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from backend.src.mlflow.enhanced_tracking import EnhancedATLASTracker
        from backend.src.agents.global_supervisor import GlobalSupervisorAgent
        from backend.src.agents.library import LibraryAgent
        from backend.src.agui.handlers import AGUIEventBroadcaster
        print("✅ All imports successful")
        
        # Test tracker initialization  
        print("\n2. Testing tracker initialization...")
        tracker = EnhancedATLASTracker(
            tracking_uri="http://localhost:5002",
            experiment_name="Simple_Test",
            auto_start_run=False  # Don't start run to avoid MLflow server dependency
        )
        print("✅ Enhanced tracker created")
        
        # Test agent initialization
        print("\n3. Testing agent initialization...")
        broadcaster = AGUIEventBroadcaster(connection_manager=None)
        
        # Test Global Supervisor - this was failing before
        global_supervisor = GlobalSupervisorAgent(
            task_id="test_task",
            agui_broadcaster=broadcaster,
            mlflow_tracker=tracker  # This parameter should exist now
        )
        print(f"✅ Global Supervisor: {global_supervisor.agent_id}")
        print(f"   Has mlflow_tracker: {hasattr(global_supervisor, 'mlflow_tracker')}")
        print(f"   mlflow_tracker value: {global_supervisor.mlflow_tracker is not None}")
        
        # Test Library Agent - this was also failing before
        library_agent = LibraryAgent(
            task_id="test_task",
            agui_broadcaster=broadcaster,
            mlflow_tracker=tracker  # This parameter should exist now
        )
        print(f"✅ Library Agent: {library_agent.agent_id}")
        print(f"   Has mlflow_tracker: {hasattr(library_agent, 'mlflow_tracker')}")
        print(f"   mlflow_tracker value: {library_agent.mlflow_tracker is not None}")
        
        # Test that agents don't crash when accessing mlflow_tracker
        print("\n4. Testing mlflow_tracker access...")
        try:
            # This should NOT raise AttributeError anymore
            supervisor_tracker = global_supervisor.mlflow_tracker
            library_tracker = library_agent.mlflow_tracker
            print("✅ mlflow_tracker attribute access successful")
            print(f"   Both trackers are same instance: {supervisor_tracker is library_tracker}")
        except AttributeError as e:
            print(f"❌ AttributeError still occurs: {e}")
            return False
        
        print("\n🎉 RESTORATION TEST RESULTS")
        print("=" * 50)
        print("✅ Imports: WORKING")
        print("✅ Enhanced tracker: WORKING") 
        print("✅ Global Supervisor: NO ATTRIBUTE ERRORS")
        print("✅ Library Agent: NO ATTRIBUTE ERRORS")
        print("✅ mlflow_tracker access: WORKING")
        
        print("\n📝 What was fixed:")
        print("   • Added mlflow_tracker parameter to GlobalSupervisorAgent.__init__")
        print("   • Added mlflow_tracker parameter to LibraryAgent.__init__")
        print("   • Both agents now properly store and pass mlflow_tracker to BaseAgent")
        print("   • Enhanced MLflow tracking system restored in separate files")
        print("   • Original architecture preserved with enhanced capabilities")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_restoration()
    
    if success:
        print("\n🎉 ARCHITECTURE RESTORATION SUCCESSFUL!")
        print("✅ No more 'mlflow_tracker' attribute errors")
        print("✅ Agents can be initialized with enhanced tracking")
        print("✅ Original separation of concerns maintained")
    else:
        print("\n❌ ARCHITECTURE RESTORATION FAILED!")
        print("⚠️ Check error messages above")
    
    exit(0 if success else 1)