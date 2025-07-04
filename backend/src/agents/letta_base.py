"""
Module: letta_base
Purpose: Integrates Letta agents with ATLAS BaseAgent
Dependencies: letta client, BaseAgent
Used By: All supervisor and worker agents
"""

from typing import Dict, Any, Optional, List
import logging
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class LettaAgentMixin:
    """
    Adds Letta persistent memory capabilities to ATLAS agents.
    
    Key responsibilities:
    - Create/retrieve Letta agents
    - Send messages with tool support
    - Extract tool calls from responses
    
    Integrations:
    - Letta: Provides persistent memory
    - BaseAgent: Inherits tracking/broadcasting
    - AG-UI: Broadcasts memory updates
    """
    
    def __init__(self, *args, **kwargs):
        # Initialize parent class first
        super().__init__(*args, **kwargs)
        
        # Then initialize Letta-specific attributes
        self._init_letta_attributes()
    
    def _init_letta_attributes(self):
        """Initialize Letta-specific attributes"""
        self.letta_base_url = "http://localhost:8283"
        self.letta_agent_id = None
        self.letta_user_id = "atlas_system"
        
    async def initialize_letta_agent(self, tools: List[Dict] = None):
        """Create or retrieve Letta agent with tools"""
        
        try:
            # Check if agent exists
            async with httpx.AsyncClient() as client:
                # List agents
                agents_response = await client.get(
                    f"{self.letta_base_url}/v1/agents",
                    headers={"accept": "application/json"}
                )
                
                if agents_response.status_code == 200:
                    agents = agents_response.json()
                    for agent in agents:
                        if agent.get("name") == self.agent_id:
                            self.letta_agent_id = agent["id"]
                            logger.info(f"Retrieved existing Letta agent: {self.agent_id} (ID: {self.letta_agent_id})")
                            return
                
                # Create new agent if not found
                create_payload = {
                    "name": self.agent_id,
                    "agent_type": "memgpt_agent",
                    "llm_config": {
                        "model": "gpt-4",
                        "model_endpoint_type": "openai",
                        "model_endpoint": "https://api.openai.com/v1",
                        "context_window": 8192
                    },
                    "embedding_config": {
                        "embedding_endpoint_type": "openai",
                        "embedding_endpoint": "https://api.openai.com/v1",
                        "embedding_model": "text-embedding-ada-002"
                    },
                    "system": self.persona if hasattr(self, 'persona') else f"You are {self.agent_id}, an agent in the ATLAS system.",
                    "tools": tools or [],
                    "include_base_tools": True
                }
                
                create_response = await client.post(
                    f"{self.letta_base_url}/v1/agents",
                    json=create_payload,
                    headers={"accept": "application/json", "Content-Type": "application/json"}
                )
                
                if create_response.status_code in [200, 201]:
                    agent_data = create_response.json()
                    self.letta_agent_id = agent_data["id"]
                    logger.info(f"Created new Letta agent: {self.agent_id} (ID: {self.letta_agent_id})")
                else:
                    logger.error(f"Failed to create Letta agent: {create_response.status_code} - {create_response.text}")
                    
        except Exception as e:
            logger.error(f"Error initializing Letta agent: {e}")
            # Continue without Letta if server is down
            self.letta_agent_id = None
    
    async def send_to_letta(self, message: str, stream: bool = False) -> Dict[str, Any]:
        """Send message to Letta and get response with tool calls"""
        
        if not self.letta_agent_id:
            await self.initialize_letta_agent()
            
        if not self.letta_agent_id:
            # Fallback if Letta is unavailable
            logger.warning("Letta agent not available, using fallback response")
            return {
                "content": "I understand your request, but I'm currently unable to access my persistent memory. Processing with limited context.",
                "tool_calls": [],
                "raw_response": None
            }
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Send message to Letta
                message_payload = {
                    "message": message,
                    "stream": stream,
                    "role": "user"
                }
                
                response = await client.post(
                    f"{self.letta_base_url}/v1/agents/{self.letta_agent_id}/messages",
                    json=message_payload,
                    headers={"accept": "application/json", "Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Extract tool calls if present
                    tool_calls = []
                    messages = response_data.get("messages", [])
                    
                    for msg in messages:
                        if msg.get("tool_calls"):
                            for tc in msg["tool_calls"]:
                                tool_calls.append({
                                    "id": tc.get("id"),
                                    "name": tc.get("function", {}).get("name"),
                                    "arguments": tc.get("function", {}).get("arguments", {})
                                })
                    
                    # Get the assistant's response
                    assistant_message = ""
                    for msg in messages:
                        if msg.get("role") == "assistant" and msg.get("text"):
                            assistant_message = msg["text"]
                            break
                    
                    return {
                        "content": assistant_message,
                        "tool_calls": tool_calls,
                        "raw_response": response_data,
                        "usage": response_data.get("usage", {})
                    }
                else:
                    logger.error(f"Letta message failed: {response.status_code} - {response.text}")
                    return {
                        "content": f"Error communicating with Letta: {response.status_code}",
                        "tool_calls": [],
                        "raw_response": None
                    }
                    
        except Exception as e:
            logger.error(f"Error sending message to Letta: {e}")
            return {
                "content": "Error processing request with persistent memory.",
                "tool_calls": [],
                "raw_response": None
            }
    
    async def load_conversation_context(self, chat_history: List[Dict[str, Any]]):
        """Load previous conversation history into Letta agent"""
        
        if not self.letta_agent_id:
            await self.initialize_letta_agent()
            
        if not self.letta_agent_id or not chat_history:
            return
            
        try:
            # Format chat history as context message
            context_parts = ["Previous conversation context:"]
            
            for msg in chat_history[-10:]:  # Last 10 messages for context
                timestamp = msg.get("timestamp", "")
                msg_type = msg.get("message_type", "")
                content = msg.get("content", "")
                
                if msg_type == "user":
                    context_parts.append(f"User ({timestamp}): {content}")
                elif msg_type == "agent":
                    agent_id = msg.get("agent_id", "assistant")
                    context_parts.append(f"{agent_id} ({timestamp}): {content}")
            
            context_message = "\n".join(context_parts)
            
            # Send context to Letta as a system message
            await self.send_to_letta(
                f"[SYSTEM CONTEXT LOAD]\n{context_message}\n[END CONTEXT]"
            )
            
            logger.info(f"Loaded {len(chat_history)} messages into Letta context")
            
        except Exception as e:
            logger.error(f"Error loading conversation context: {e}")
    
    async def update_memory(self, key: str, value: Any):
        """Update specific memory in Letta agent"""
        
        if not self.letta_agent_id:
            return
            
        try:
            # Use Letta's memory update through a special message format
            memory_update = f"[MEMORY UPDATE] {key}: {value}"
            await self.send_to_letta(memory_update)
            
            logger.info(f"Updated Letta memory: {key}")
            
        except Exception as e:
            logger.error(f"Error updating Letta memory: {e}")
    
    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get Letta agent statistics and memory usage"""
        
        if not self.letta_agent_id:
            return {}
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.letta_base_url}/v1/agents/{self.letta_agent_id}",
                    headers={"accept": "application/json"}
                )
                
                if response.status_code == 200:
                    agent_data = response.json()
                    return {
                        "memory_usage": agent_data.get("memory", {}),
                        "message_count": agent_data.get("message_count", 0),
                        "created_at": agent_data.get("created_at"),
                        "last_updated": agent_data.get("updated_at")
                    }
                    
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            
        return {}