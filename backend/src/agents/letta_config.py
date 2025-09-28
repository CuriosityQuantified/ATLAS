"""
Configuration for local Letta server with Web ADE (Agent Development Environment)

This module provides configuration and utilities for running Letta agents locally
with full visibility through the Web ADE at https://app.letta.com
"""

import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Local Letta Server Configuration
LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
LETTA_API_KEY = None  # No API key needed for local mode
LETTA_LOCAL_MODE = os.getenv("LETTA_LOCAL_MODE", "true").lower() == "true"

# Web ADE Configuration
LETTA_ADE_URL = "https://app.letta.com"  # Web ADE for debugging and development

def check_server_health() -> bool:
    """
    Verify that the local Letta server is running and accessible.

    Returns:
        bool: True if server is healthy, False otherwise
    """
    try:
        response = requests.get(
            f"{LETTA_BASE_URL}/v1/health",
            timeout=5
        )
        if response.status_code == 200:
            logger.info(f"Letta server is healthy at {LETTA_BASE_URL}")
            return True
        else:
            logger.warning(f"Letta server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(
            f"Cannot connect to Letta server at {LETTA_BASE_URL}. "
            "Please start it with: letta server"
        )
        return False
    except Exception as e:
        logger.error(f"Error checking Letta server health: {e}")
        return False

def get_ade_connection_info() -> Dict[str, Any]:
    """
    Get information for connecting the Web ADE to the local Letta server.

    Returns:
        dict: Connection information and instructions
    """
    return {
        "ade_url": LETTA_ADE_URL,
        "server_url": LETTA_BASE_URL,
        "local_mode": LETTA_LOCAL_MODE,
        "instructions": [
            f"1. Open {LETTA_ADE_URL} in your browser",
            "2. Sign in with GitHub, Google, or email",
            "3. Click 'Self-hosted' tab in the left panel",
            f"4. Enter server URL: {LETTA_BASE_URL}",
            "5. Click 'Connect' to link ADE to your local server"
        ],
        "features": [
            "Agent Simulator - Interactive testing with real-time monitoring",
            "Memory Inspector - View and edit agent memory blocks",
            "Tool Editor - Write and test Python tools in browser",
            "Context Window - See exactly what the LLM sees",
            "System Instructions - Configure agent behavior without code"
        ]
    }

def get_server_config() -> Dict[str, Any]:
    """
    Get the current server configuration for use with Letta client.

    Returns:
        dict: Server configuration parameters
    """
    config = {
        "base_url": LETTA_BASE_URL,
        "api_key": LETTA_API_KEY,
        "local_mode": LETTA_LOCAL_MODE
    }

    if LETTA_LOCAL_MODE:
        logger.info(f"Using local Letta server at {LETTA_BASE_URL}")
    else:
        logger.info("Using Letta Cloud API")

    return config

def print_startup_info():
    """
    Print helpful startup information for developers.
    """
    print("\n" + "="*60)
    print("ATLAS - Letta Local Server Configuration")
    print("="*60)
    print(f"Server URL: {LETTA_BASE_URL}")
    print(f"Local Mode: {LETTA_LOCAL_MODE}")
    print(f"Server Health: {'✓ Connected' if check_server_health() else '✗ Not Connected'}")

    if not check_server_health():
        print("\n⚠️  Letta server is not running!")
        print("Start it with: letta server")

    print("\n📊 Web ADE Access:")
    for instruction in get_ade_connection_info()["instructions"]:
        print(f"  {instruction}")

    print("\n🛠️  Available ADE Features:")
    for feature in get_ade_connection_info()["features"]:
        print(f"  • {feature}")

    print("="*60 + "\n")

def validate_environment() -> bool:
    """
    Validate that the environment is properly configured for local Letta operation.

    Returns:
        bool: True if environment is valid, False otherwise
    """
    issues = []

    # Check if running in local mode
    if not LETTA_LOCAL_MODE:
        issues.append("LETTA_LOCAL_MODE is not set to 'true'")

    # Check if server URL is local
    if not LETTA_BASE_URL.startswith(("http://localhost", "http://127.0.0.1")):
        issues.append(f"LETTA_SERVER_URL '{LETTA_BASE_URL}' is not a local address")

    # Check if API key is not set (should be None for local mode)
    if LETTA_LOCAL_MODE and os.getenv("LETTA_API_KEY"):
        logger.warning("LETTA_API_KEY is set but not needed for local mode")

    # Check server health
    if not check_server_health():
        issues.append("Letta server is not responding")

    if issues:
        logger.error("Environment validation failed:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False

    logger.info("Environment validation passed ✓")
    return True

# Tool registration helpers for Phase 2
def get_tool_registration_template() -> Dict[str, Any]:
    """
    Get a template for registering tools with Letta agents.
    This will be used in Phase 2 for tool-based architecture.

    Returns:
        dict: Tool registration template
    """
    return {
        "planning_tool": {
            "name": "plan_task",
            "description": "Decompose complex tasks into structured plans",
            "parameters": ["task", "context"],
            "returns": "structured_plan"
        },
        "research_tool": {
            "name": "call_research_agent",
            "description": "Invoke research agent for information gathering",
            "parameters": ["query", "context"],
            "returns": "research_results"
        },
        "analysis_tool": {
            "name": "call_analysis_agent",
            "description": "Invoke analysis agent for data interpretation",
            "parameters": ["data", "framework"],
            "returns": "analysis_results"
        },
        "writing_tool": {
            "name": "call_writing_agent",
            "description": "Invoke writing agent for content generation",
            "parameters": ["content", "style"],
            "returns": "written_output"
        },
        "file_tools": {
            "create": "create_file",
            "read": "read_file",
            "update": "update_file",
            "description": "File operation tools for agents"
        }
    }

if __name__ == "__main__":
    # Run validation and print info when module is executed directly
    print_startup_info()
    validate_environment()