"""Letta service for managing persistent AI agents."""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from pathlib import Path

from letta import RESTClient
from letta import AgentState, Message

from .models import LettaAgent, LettaAgentConfig, LettaMessage, LettaConversation, AgentStatus
from .conversation_persistence import conversation_persistence
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class LettaService:
    """Service for managing Letta agents."""
    
    def __init__(self):
        """Initialize Letta service."""
        self.client = None
        self.agents_cache: Dict[str, Any] = {}
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Letta client."""
        try:
            # Connect to local Letta server
            base_url = os.environ.get("LETTA_SERVER_URL", "http://localhost:8283")
            self.client = RESTClient(base_url=base_url)
            logger.info(f"Letta REST client initialized successfully with {base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Letta client: {e}")
            raise
    
    async def create_agent(self, config: LettaAgentConfig) -> LettaAgent:
        """Create a new Letta agent."""
        try:
            # Create agent using new Letta API
            from letta.schemas.memory import ChatMemory
            
            # Create memory with persona and human
            memory = ChatMemory(
                persona=config.persona or f"You are {config.name}, a helpful AI assistant.",
                human=config.human or "User",
                limit=5000
            )
            
            # Create agent using new API
            from letta.schemas.llm_config import LLMConfig
            from letta.schemas.embedding_config import EmbeddingConfig
            
            # Create LLM config
            llm_config = LLMConfig(
                model=config.model or "gpt-4",
                model_endpoint_type="openai",
                model_endpoint="https://api.openai.com/v1",
                context_window=8192  # Default context window for GPT-4
            )
            
            # Create embedding config (using default OpenAI settings)
            embedding_config = EmbeddingConfig.default_config(
                model_name="text-embedding-ada-002",
                provider="openai"
            )
            
            agent = self.client.create_agent(
                name=config.name,
                memory=memory,
                llm_config=llm_config,
                embedding_config=embedding_config,
                description=config.description,
                metadata={"preset": config.preset} if config.preset else {}
            )
            
            # Cache the agent
            self.agents_cache[agent.id] = agent
            
            # Convert to our model
            return LettaAgent(
                id=agent.id,
                name=agent.name,
                description=config.description,
                status=AgentStatus.ACTIVE,
                model=config.model,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                memory_stats=self._get_memory_stats(agent),
                metadata={"preset": config.preset}
            )
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[LettaAgent]:
        """Get an agent by ID."""
        try:
            # Check cache first
            if agent_id in self.agents_cache:
                agent = self.agents_cache[agent_id]
            else:
                # Load from Letta
                agent = self.client.get_agent(agent_id)
                if agent:
                    self.agents_cache[agent_id] = agent
            
            if not agent:
                return None
            
            # Convert to our model
            return LettaAgent(
                id=agent.id,
                name=agent.name,
                description=getattr(agent, "description", None),
                status=AgentStatus.ACTIVE,
                model=getattr(agent, "model", "gpt-4"),  # Use getattr for model
                created_at=agent.created_at,
                updated_at=datetime.utcnow(),
                memory_stats=self._get_memory_stats(agent),
                metadata={}
            )
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    async def list_agents(self) -> List[LettaAgent]:
        """List all agents."""
        try:
            agents = self.client.list_agents()
            return [
                LettaAgent(
                    id=agent.id,
                    name=agent.name,
                    description=getattr(agent, "description", None),
                    status=AgentStatus.ACTIVE,
                    model=getattr(agent, "model", "gpt-4"),  # Use getattr for model
                    created_at=agent.created_at,
                    updated_at=datetime.utcnow(),
                    memory_stats={},
                    metadata={}
                )
                for agent in agents
            ]
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []
    
    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[LettaAgent]:
        """Update an agent."""
        try:
            # Get the agent
            agent = await self.get_agent(agent_id)
            if not agent:
                return None
            
            # Update agent fields
            if "name" in updates:
                self.client.update_agent(agent_id, name=updates["name"])
            
            if "description" in updates:
                # Store in metadata since Letta doesn't have description field
                agent.metadata["description"] = updates["description"]
            
            # Clear cache to force reload
            self.agents_cache.pop(agent_id, None)
            
            # Return updated agent
            return await self.get_agent(agent_id)
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            return None
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        try:
            self.client.delete_agent(agent_id)
            self.agents_cache.pop(agent_id, None)
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            return False
    
    async def send_message(self, agent_id: str, message: str) -> Optional[LettaMessage]:
        """Send a message to an agent and get response."""
        try:
            # Get or load agent
            if agent_id not in self.agents_cache:
                agent = self.client.get_agent(agent_id)
                if not agent:
                    return None
                self.agents_cache[agent_id] = agent
            else:
                agent = self.agents_cache[agent_id]
            
            # Store user message in our custom persistence
            await conversation_persistence.store_message(
                agent_id=agent_id,
                role="user",
                content=message,
                tokens_used=len(message.split()),  # Rough token estimate
                metadata={"source": "user_input"}
            )
            
            # Send message and get response
            response = self.client.user_message(agent_id=agent_id, message=message)
            
            # Extract assistant message from response
            assistant_content = ""
            if response and hasattr(response, 'messages'):
                for msg in response.messages:
                    # Check if this is an assistant message
                    if hasattr(msg, '__class__') and 'assistant' in msg.__class__.__name__.lower():
                        # Extract content - it's directly a string for AssistantMessage
                        if hasattr(msg, 'content'):
                            assistant_content = msg.content if isinstance(msg.content, str) else str(msg.content)
                        break
            
            # If we found assistant content, store it and return it
            if assistant_content:
                # Store assistant response in our custom persistence
                message_id = await conversation_persistence.store_message(
                    agent_id=agent_id,
                    role="assistant",
                    content=assistant_content,
                    tokens_used=len(assistant_content.split()),  # Rough token estimate
                    metadata={"source": "letta_response"}
                )
                
                return LettaMessage(
                    id=message_id or str(datetime.utcnow().timestamp()),
                    agent_id=agent_id,
                    role="assistant",
                    content=assistant_content,
                    timestamp=datetime.utcnow(),
                    metadata={"source": "letta_response"}
                )
            
            return None
        except Exception as e:
            logger.error(f"Failed to send message to agent {agent_id}: {e}")
            return None
    
    async def get_conversation_history(self, agent_id: str, limit: int = 50) -> LettaConversation:
        """Get conversation history for an agent."""
        try:
            # First, try to get conversation history from our custom persistence
            conversation_messages = await conversation_persistence.get_conversation_history(agent_id, limit)
            
            # If we have messages from our persistence, use them
            if conversation_messages:
                logger.debug(f"Retrieved {len(conversation_messages)} messages from custom persistence for agent {agent_id}")
                return LettaConversation(
                    agent_id=agent_id,
                    messages=conversation_messages,
                    created_at=datetime.utcnow(),
                    metadata={"source": "custom_persistence"}
                )
            
            # Fall back to Letta's conversation history (legacy behavior)
            logger.debug(f"No messages in custom persistence, falling back to Letta history for agent {agent_id}")
            
            # Get in-context messages which have full content
            messages = self.client.get_in_context_messages(agent_id)
            
            # Convert to our format
            conversation_messages = []
            processed_ids = set()  # Track processed message IDs to avoid duplicates
            
            for i, msg in enumerate(messages):
                # Skip system messages
                if hasattr(msg, 'role') and str(msg.role) == 'MessageRole.system':
                    continue
                
                msg_id = getattr(msg, 'id', str(datetime.utcnow().timestamp()))
                if msg_id in processed_ids:
                    continue
                
                # Extract text content from content list
                content_text = ""
                if hasattr(msg, 'content') and msg.content:
                    # Check if content is a list
                    if isinstance(msg.content, list):
                        for content_item in msg.content:
                            if hasattr(content_item, 'text'):
                                content_text = content_item.text
                                break
                            elif isinstance(content_item, dict) and 'text' in content_item:
                                content_text = content_item['text']
                                break
                    # If content is a string, use it directly
                    elif isinstance(msg.content, str):
                        content_text = msg.content
                
                # Map MessageRole to simple role string
                role = None
                if hasattr(msg, 'role'):
                    role_str = str(msg.role)
                    if 'user' in role_str.lower():
                        role = "user"
                    elif 'assistant' in role_str.lower():
                        role = "assistant"
                        # If assistant message is empty or a JSON status, skip it
                        if not content_text or content_text.startswith('{"status"') or '"status": "OK"' in content_text:
                            continue
                    elif 'tool' in role_str.lower():
                        # Skip tool messages that are just status confirmations
                        if content_text.startswith('{"status"') or '"status": "OK"' in content_text:
                            continue
                        # For other tool messages, treat as assistant responses
                        tool_content = self._extract_tool_content(msg)
                        if tool_content:
                            content_text = tool_content
                            role = "assistant"
                
                # Only add messages with content and valid role
                if content_text and role in ["user", "assistant"]:
                    # Skip JSON status messages
                    if content_text.startswith('{"status"') or '"status": "OK"' in content_text:
                        continue
                    
                    conversation_messages.append(
                        LettaMessage(
                            id=msg_id,
                            agent_id=agent_id,
                            role=role,
                            content=content_text,
                            timestamp=getattr(msg, 'created_at', datetime.utcnow()),
                            metadata={"source": "letta_fallback"}
                        )
                    )
                    processed_ids.add(msg_id)
            
            # Limit messages if needed
            if limit and len(conversation_messages) > limit:
                conversation_messages = conversation_messages[-limit:]
            
            return LettaConversation(
                agent_id=agent_id,
                messages=conversation_messages,
                created_at=datetime.utcnow(),
                metadata={"source": "letta_fallback"}
            )
        except Exception as e:
            logger.error(f"Failed to get conversation history for agent {agent_id}: {e}")
            return LettaConversation(agent_id=agent_id)
    
    def _extract_tool_content(self, msg: Any) -> Optional[str]:
        """Extract content from tool messages."""
        try:
            # Check if this is a tool message with content
            if hasattr(msg, 'tool_call_id') or (hasattr(msg, 'role') and 'tool' in str(msg.role).lower()):
                # Try to extract content from various possible structures
                if hasattr(msg, 'content'):
                    if isinstance(msg.content, str):
                        # Parse the content to find the actual response
                        content = msg.content
                        logger.debug(f"Tool message content: {content}")
                        
                        # Look for send_message tool response pattern
                        if "send_message" in content:
                            # Extract the actual message sent
                            import json
                            try:
                                # Try to parse as JSON
                                parsed = json.loads(content)
                                if isinstance(parsed, dict) and 'message' in parsed:
                                    return parsed['message']
                            except:
                                # If not JSON, look for patterns in the string
                                # Common pattern: "Sent message: <actual message>"
                                if "Sent message:" in content:
                                    return content.split("Sent message:", 1)[1].strip()
                                # Another pattern: just return the content if it looks like a response
                                if len(content) > 10 and not content.startswith("{"):
                                    return content
                        
                        # Skip JSON status messages
                        if content.startswith('{"status"') or '"status": "OK"' in content:
                            return None
                        
                        return content
                    elif isinstance(msg.content, list):
                        # Extract from content list
                        for item in msg.content:
                            if hasattr(item, 'text'):
                                return item.text
                            elif isinstance(item, dict) and 'text' in item:
                                return item['text']
            return None
        except Exception as e:
            logger.debug(f"Failed to extract tool content: {e}")
            return None
    
    def _get_memory_stats(self, agent: Any) -> Dict[str, Any]:
        """Get memory statistics for an agent."""
        try:
            # Get memory stats from agent
            memory = agent.memory if hasattr(agent, "memory") else None
            if memory:
                return {
                    "core_memory_size": len(str(memory.core_memory)) if hasattr(memory, "core_memory") else 0,
                    "recall_memory_size": len(str(memory.recall_memory)) if hasattr(memory, "recall_memory") else 0,
                    "archival_memory_size": len(str(memory.archival_memory)) if hasattr(memory, "archival_memory") else 0,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}


# Singleton instance
letta_service = LettaService()