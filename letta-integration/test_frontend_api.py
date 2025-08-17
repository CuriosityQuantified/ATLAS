#!/usr/bin/env python3
"""Test script to verify frontend can access Letta agents via backend API."""

import requests
import json

# Test backend API endpoints
BACKEND_URL = "http://localhost:8001"

def test_backend_health():
    """Test backend health endpoint."""
    print("Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print("✓ Backend is healthy")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to connect to backend: {e}")

def test_letta_agents():
    """Test Letta agents endpoint."""
    print("\nTesting Letta agents endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/letta/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✓ Found {len(agents)} agent(s)")
            for agent in agents:
                print(f"\n  Agent: {agent['name']}")
                print(f"  ID: {agent['id']}")
                print(f"  Model: {agent['model']}")
                print(f"  Status: {agent['status']}")
                print(f"  Created: {agent['created_at']}")
        else:
            print(f"✗ Failed to get agents: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to fetch agents: {e}")

def test_agent_details(agent_id):
    """Test getting specific agent details."""
    print(f"\nTesting agent details for {agent_id}...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/letta/agents/{agent_id}")
        if response.status_code == 200:
            agent = response.json()
            print("✓ Successfully retrieved agent details")
            print(f"  Name: {agent['name']}")
            print(f"  Description: {agent.get('description', 'N/A')}")
        else:
            print(f"✗ Failed to get agent details: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to fetch agent details: {e}")

if __name__ == "__main__":
    print("=== Testing Frontend API Access ===\n")
    
    # Test backend health
    test_backend_health()
    
    # Test Letta agents
    test_letta_agents()
    
    # Test specific agent (if exists)
    test_agent_details("agent-d4e261c1-c93c-48ba-bce5-a72025df50de")
    
    print("\n=== Test Complete ===")