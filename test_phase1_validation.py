#!/usr/bin/env python3
"""
Phase 1 Complete Validation Script
Verifies all Phase 1 components are properly configured and operational
"""

import sys
import os
import requests
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)

def test_server_connectivity():
    """Test that Letta server is reachable."""
    print("\n🔍 Testing Server Connectivity...")

    try:
        response = requests.get("http://localhost:8283/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running at http://localhost:8283")
            return True
        else:
            print(f"⚠️  Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not reachable: {e}")
        print("   Run: ./scripts/dev/start-letta-with-ade.sh")
        return False

def test_agent_operations():
    """Test agent creation and interaction."""
    print("\n🤖 Testing Agent Operations...")

    try:
        from agents.agent_factory import LettaAgentFactory

        # Create factory
        factory = LettaAgentFactory()
        print("✅ Agent factory initialized")

        # List agents
        agents = factory.list_agents()
        print(f"✅ Found {len(agents)} existing agents")

        # Create test agent
        test_agent = factory.create_supervisor_agent("phase1_test")
        print(f"✅ Created test agent: {test_agent.name}")

        # Send message
        response = factory.send_message_to_agent(
            test_agent.id,
            "Respond with 'Phase 1 validated successfully'"
        )
        if response:
            print(f"✅ Agent responded: {response[0][:100]}...")

        # Clean up
        factory.delete_agent(test_agent.id)
        print("✅ Test agent deleted")

        return True

    except Exception as e:
        print(f"❌ Agent operations failed: {e}")
        return False

def check_file_structure():
    """Verify all Phase 1 files exist."""
    print("\n📁 Checking File Structure...")

    files_to_check = {
        "backend/src/agents/letta_config.py": "Letta configuration module",
        "backend/src/agents/agent_factory.py": "Agent factory with new SDK",
        "scripts/dev/start-letta-with-ade.sh": "Server startup script",
        "backend/requirements.txt": "Updated dependencies",
        ".env.example": "Environment template",
        "PHASE1_COMPLETE.md": "Phase 1 documentation"
    }

    all_good = True
    for file_path, description in files_to_check.items():
        if Path(file_path).exists():
            print(f"✅ {file_path}: {description}")
        else:
            print(f"❌ Missing: {file_path} ({description})")
            all_good = False

    return all_good

def check_dependencies():
    """Check that all required packages are installed."""
    print("\n📦 Checking Dependencies...")

    required_packages = {
        "letta_client": "Official Letta SDK",
        "firecrawl": "Web scraping tool",
        "sqlite_vec": "SQLite vector extension"
    }

    all_good = True
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"❌ Missing: {package} ({description})")
            all_good = False

    return all_good

def print_web_ade_instructions():
    """Print instructions for connecting Web ADE."""
    print_header("Web ADE Connection Instructions")

    print("""
The Letta server is running successfully! To connect Web ADE:

OPTION 1 - Chrome with Security Bypass (Recommended):
------------------------------------------------------
Run this command to open Chrome with relaxed security:

macOS:
open -na "Google Chrome" --args --allow-insecure-localhost \\
  --disable-web-security --user-data-dir="/tmp/chrome_dev"

Then:
1. Go to https://app.letta.com
2. Click "Self-hosted" tab
3. Enter: http://localhost:8283
4. Click "Connect"

OPTION 2 - Use Built-in Letta UI:
----------------------------------
Open: http://localhost:8283

This provides basic agent management without Web ADE features.

OPTION 3 - Browser Settings:
-----------------------------
In Chrome/Brave:
1. Visit chrome://flags/#allow-insecure-localhost
2. Enable "Allow invalid certificates for localhost"
3. Restart browser
4. Try connecting Web ADE again
""")

def print_phase2_readiness():
    """Print Phase 2 readiness status."""
    print_header("Phase 2 Readiness")

    print("""
✅ PHASE 1 COMPLETE - Ready for Phase 2!

Phase 2 will implement:
- Tool-based supervisor agent architecture
- Sub-agents exposed as callable tools
- Planning and todo management tools
- File operation tools
- Full integration with Web ADE for debugging

To begin Phase 2:
1. Ensure Letta server is running
2. Review PLAN.md for Phase 2 specifications
3. Start with supervisor agent tool implementation
""")

def main():
    """Run all validation tests."""
    print_header("ATLAS Phase 1 Validation")

    # Run tests
    server_ok = test_server_connectivity()
    deps_ok = check_dependencies() if server_ok else False
    files_ok = check_file_structure()
    agents_ok = test_agent_operations() if server_ok else False

    # Summary
    print_header("Validation Summary")

    all_passed = server_ok and deps_ok and files_ok and agents_ok

    if all_passed:
        print("\n✨ ALL TESTS PASSED! Phase 1 is complete!")
        print_phase2_readiness()
    else:
        print("\n⚠️  Some tests failed. Please address the issues above.")
        print("\nKey fixes:")
        if not server_ok:
            print("  1. Start server: ./scripts/dev/start-letta-with-ade.sh")
        if not deps_ok:
            print("  2. Install deps: uv pip install -r backend/requirements.txt")
        if not files_ok:
            print("  3. Verify all Phase 1 files are created")

    # Always show Web ADE instructions
    if server_ok:
        print_web_ade_instructions()

if __name__ == "__main__":
    main()