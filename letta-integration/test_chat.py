#!/usr/bin/env python3
"""Test script to send a message to the agent."""

import asyncio
import sys
import os

# Add parent directory to path to import backend modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.src.letta.service import LettaService


async def main():
    service = LettaService()
    
    # Get the agent ID
    agent_id = "agent-d4e261c1-c93c-48ba-bce5-a72025df50de"
    
    # Send a test message
    print(f"Sending message to agent {agent_id}...")
    response = await service.send_message(agent_id, "Hello! Can you introduce yourself?")
    
    if response:
        print(f"\nAgent response: {response.content}")
    else:
        print("No response received.")


if __name__ == "__main__":
    asyncio.run(main())