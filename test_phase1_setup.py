#!/usr/bin/env python3
"""
Phase 1 Setup Validation Script
Tests the local Letta configuration and Web ADE integration
"""

import os
import sys
import requests
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

def test_dependencies():
    """Test that required dependencies are installed."""
    print("\n📦 Testing Dependencies...")

    dependencies = {
        "letta_client": "Official Letta client SDK",
        "firecrawl": "Web scraping tool",
        # "e2b_code_interpreter": "Code execution sandbox",  # Optional for now
    }

    for module_name, description in dependencies.items():
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}: {description}")
        except ImportError as e:
            print(f"  ✗ {module_name}: Not installed ({description})")
            print(f"    Error: {e}")

def test_letta_config():
    """Test the letta_config module."""
    print("\n⚙️  Testing Letta Configuration Module...")

    try:
        from agents.letta_config import (
            LETTA_BASE_URL,
            LETTA_LOCAL_MODE,
            check_server_health,
            get_ade_connection_info
        )

        print(f"  Server URL: {LETTA_BASE_URL}")
        print(f"  Local Mode: {LETTA_LOCAL_MODE}")

        # Check server health
        if check_server_health():
            print("  ✓ Letta server is running")
        else:
            print("  ⚠ Letta server is not running")
            print("    Start it with: letta server")

        # Get ADE info
        ade_info = get_ade_connection_info()
        print(f"  Web ADE URL: {ade_info['ade_url']}")

    except Exception as e:
        print(f"  ✗ Error loading letta_config: {e}")

def test_environment_variables():
    """Test that environment variables are properly set."""
    print("\n🔐 Testing Environment Variables...")

    env_vars = {
        "LETTA_SERVER_URL": ("http://localhost:8283", "Local Letta server URL"),
        "LETTA_LOCAL_MODE": ("true", "Enable local mode"),
        "MLFLOW_TRACKING_URI": ("http://localhost:5002", "MLflow tracking server"),
    }

    for var, (expected, description) in env_vars.items():
        value = os.getenv(var)
        if value:
            status = "✓" if value == expected else "⚠"
            print(f"  {status} {var}: {value} ({description})")
        else:
            print(f"  ✗ {var}: Not set ({description})")

def test_file_structure():
    """Test that all Phase 1 files are created."""
    print("\n📁 Testing File Structure...")

    files = {
        "backend/src/agents/letta_config.py": "Letta configuration module",
        "backend/src/agents/agent_factory.py": "Agent factory (updated)",
        "scripts/dev/start-letta-with-ade.sh": "Startup script",
        ".env.example": "Environment template (updated)",
        "backend/requirements.txt": "Dependencies (updated)",
    }

    for file_path, description in files.items():
        path = Path(file_path)
        if path.exists():
            print(f"  ✓ {file_path}: {description}")
        else:
            print(f"  ✗ {file_path}: Missing ({description})")

def print_instructions():
    """Print next steps for completing Phase 1."""
    print("\n" + "="*60)
    print("📋 Next Steps to Complete Phase 1:")
    print("="*60)
    print("\n1️⃣  Configure Letta (if not done):")
    print("   .venv/bin/python -m letta configure")
    print("   - Select: local storage, SQLite backend")
    print()
    print("2️⃣  Start Letta Server:")
    print("   ./scripts/dev/start-letta-with-ade.sh")
    print("   OR")
    print("   .venv/bin/python -m letta server")
    print()
    print("3️⃣  Connect Web ADE:")
    print("   - Open: https://app.letta.com")
    print("   - Go to 'Self-hosted' tab")
    print("   - Connect to: http://localhost:8283")
    print()
    print("4️⃣  Test Agent Creation:")
    print("   - Create test agent in Web ADE")
    print("   - Verify it appears in agent list")
    print()
    print("5️⃣  Start MLflow (optional):")
    print("   mlflow server --host 0.0.0.0 --port 5002")
    print()
    print("✅ Phase 1 Complete when:")
    print("   - Letta server runs locally")
    print("   - Web ADE connects successfully")
    print("   - Can create and interact with agents")
    print("="*60)

def main():
    """Run all Phase 1 validation tests."""
    print("\n" + "="*60)
    print("🚀 ATLAS Phase 1 Setup Validation")
    print("="*60)

    test_dependencies()
    test_letta_config()
    test_environment_variables()
    test_file_structure()
    print_instructions()

    print("\n✨ Phase 1 setup validation complete!")
    print("   Follow the next steps above to finish configuration.\n")

if __name__ == "__main__":
    main()