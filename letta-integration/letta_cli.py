#!/usr/bin/env python3
"""
Letta CLI for local IDE integration.
Allows creating, editing, and conversing with Letta agents from command line.
"""

import argparse
import asyncio
import json
import sys
import os
from typing import Optional
from datetime import datetime

# Add parent directory to path to import backend modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.src.letta.service import LettaService
from backend.src.letta.models import LettaAgentConfig


class LettaCLI:
    """Command line interface for Letta agent management."""
    
    def __init__(self):
        self.service = LettaService()
    
    async def list_agents(self):
        """List all agents."""
        agents = await self.service.list_agents()
        if not agents:
            print("No agents found.")
            return
        
        print(f"\n{'ID':<36} {'Name':<20} {'Model':<15} {'Status':<10} {'Created'}")
        print("-" * 100)
        for agent in agents:
            # Handle datetime conversion more carefully
            if isinstance(agent.created_at, str):
                try:
                    created_dt = datetime.fromisoformat(agent.created_at.replace('Z', '+00:00'))
                    created = created_dt.strftime('%Y-%m-%d %H:%M')
                except:
                    created = agent.created_at[:16] if len(agent.created_at) >= 16 else agent.created_at
            else:
                created = agent.created_at.strftime('%Y-%m-%d %H:%M')
            
            print(f"{agent.id:<36} {agent.name:<20} {agent.model:<15} {agent.status.value:<10} {created}")
    
    async def create_agent(self, name: str, model: str = "gpt-4", 
                          persona: Optional[str] = None, 
                          description: Optional[str] = None):
        """Create a new agent."""
        config = LettaAgentConfig(
            name=name,
            model=model,
            persona=persona or f"You are {name}, a helpful AI assistant.",
            description=description,
            human="User"
        )
        
        print(f"Creating agent '{name}'...")
        agent = await self.service.create_agent(config)
        print(f"✓ Agent created successfully!")
        print(f"  ID: {agent.id}")
        print(f"  Name: {agent.name}")
        print(f"  Model: {agent.model}")
    
    async def delete_agent(self, agent_id: str):
        """Delete an agent."""
        if not await self._confirm_action(f"Delete agent {agent_id}"):
            return
        
        success = await self.service.delete_agent(agent_id)
        if success:
            print("✓ Agent deleted successfully!")
        else:
            print("✗ Failed to delete agent.")
    
    async def chat(self, agent_id: str):
        """Start interactive chat with an agent."""
        # Get agent details
        agent = await self.service.get_agent(agent_id)
        if not agent:
            print(f"Agent {agent_id} not found.")
            return
        
        print(f"\nStarting chat with {agent.name} (ID: {agent_id})")
        print("Type 'exit' or 'quit' to end the conversation.\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("\nEnding conversation. Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Send message and get response
                print(f"{agent.name}: ", end="", flush=True)
                response = await self.service.send_message(agent_id, user_input)
                
                if response:
                    print(response.content)
                else:
                    print("(No response)")
                
                print()  # Empty line for readability
                
            except KeyboardInterrupt:
                print("\n\nConversation interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
    
    async def show_history(self, agent_id: str, limit: int = 20):
        """Show conversation history for an agent."""
        conversation = await self.service.get_conversation_history(agent_id, limit)
        
        if not conversation.messages:
            print("No conversation history found.")
            return
        
        print(f"\nConversation history (last {limit} messages):")
        print("-" * 80)
        
        for msg in conversation.messages:
            timestamp = datetime.fromisoformat(msg.timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            role = "You" if msg.role == "user" else conversation.agent_id
            print(f"[{timestamp}] {role}: {msg.content}")
            print()
    
    async def export_agent(self, agent_id: str, output_file: str):
        """Export agent configuration to JSON file."""
        agent = await self.service.get_agent(agent_id)
        if not agent:
            print(f"Agent {agent_id} not found.")
            return
        
        # Get conversation history
        conversation = await self.service.get_conversation_history(agent_id, limit=1000)
        
        export_data = {
            "agent": agent.dict(),
            "conversation": conversation.dict()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✓ Agent exported to {output_file}")
    
    def _confirm_action(self, action: str) -> bool:
        """Confirm a destructive action."""
        response = input(f"Are you sure you want to {action}? (y/N): ")
        return response.lower() == 'y'


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Letta CLI for agent management")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    subparsers.add_parser("list", help="List all agents")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new agent")
    create_parser.add_argument("name", help="Agent name")
    create_parser.add_argument("--model", default="gpt-4", help="LLM model to use")
    create_parser.add_argument("--persona", help="Agent persona/system prompt")
    create_parser.add_argument("--description", help="Agent description")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete an agent")
    delete_parser.add_argument("agent_id", help="Agent ID to delete")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with an agent")
    chat_parser.add_argument("agent_id", help="Agent ID to chat with")
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show conversation history")
    history_parser.add_argument("agent_id", help="Agent ID")
    history_parser.add_argument("--limit", type=int, default=20, help="Number of messages to show")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export agent to JSON")
    export_parser.add_argument("agent_id", help="Agent ID to export")
    export_parser.add_argument("output_file", help="Output JSON file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = LettaCLI()
    
    try:
        if args.command == "list":
            await cli.list_agents()
        elif args.command == "create":
            await cli.create_agent(
                args.name, 
                args.model, 
                args.persona, 
                args.description
            )
        elif args.command == "delete":
            await cli.delete_agent(args.agent_id)
        elif args.command == "chat":
            await cli.chat(args.agent_id)
        elif args.command == "history":
            await cli.show_history(args.agent_id, args.limit)
        elif args.command == "export":
            await cli.export_agent(args.agent_id, args.output_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())