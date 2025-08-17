"""Custom conversation persistence for Letta agents.

This module provides a persistence layer that stores actual assistant responses
from Letta agents, which are not persisted in Letta's own conversation history.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import asyncpg

from .models import LettaMessage, LettaConversation
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class LettaConversationPersistence:
    """Persistence layer for Letta conversations using PostgreSQL."""
    
    def __init__(self):
        """Initialize the persistence layer."""
        self.pool: Optional[asyncpg.Pool] = None
        self.settings = get_settings()
        
    async def initialize(self):
        """Initialize the database connection pool."""
        try:
            # Connect to atlas_agents database
            dsn = f"postgresql://{self.settings.ATLAS_AGENTS_USER}:{self.settings.ATLAS_AGENTS_PASSWORD}@{self.settings.POSTGRES_HOST}:{self.settings.POSTGRES_PORT}/atlas_agents"
            self.pool = await asyncpg.create_pool(dsn, min_size=1, max_size=10)
            logger.info("Letta conversation persistence initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize conversation persistence: {e}")
            raise
    
    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def create_session(self, agent_id: str, task_id: Optional[str] = None) -> str:
        """Create a new agent session.
        
        Args:
            agent_id: The Letta agent ID
            task_id: Optional task ID for associating with ATLAS tasks
            
        Returns:
            The session ID as a string
        """
        try:
            if not self.pool:
                await self.initialize()
            
            # Generate UUIDs
            session_uuid = uuid4()
            agent_uuid = self._extract_uuid_from_agent_id(agent_id)
            task_uuid = UUID(task_id) if task_id and self._is_valid_uuid(task_id) else uuid4()
            
            async with self.pool.acquire() as conn:
                # Use the stored function to create session
                session_id = await conn.fetchval(
                    "SELECT create_agent_session($1, $2, $3)",
                    agent_uuid, task_uuid, '{}'
                )
                
                logger.info(f"Created agent session {session_id} for agent {agent_id}")
                return str(session_id)
                
        except Exception as e:
            logger.error(f"Failed to create session for agent {agent_id}: {e}")
            raise
    
    async def get_session_id(self, agent_id: str) -> Optional[str]:
        """Get the active session ID for an agent.
        
        Args:
            agent_id: The Letta agent ID
            
        Returns:
            The active session ID or None if no active session
        """
        try:
            if not self.pool:
                await self.initialize()
            
            agent_uuid = self._extract_uuid_from_agent_id(agent_id)
                
            async with self.pool.acquire() as conn:
                session_id = await conn.fetchval(
                    """
                    SELECT session_id FROM agent_sessions 
                    WHERE agent_id = $1 AND is_active = true 
                    ORDER BY started_at DESC 
                    LIMIT 1
                    """,
                    agent_uuid
                )
                
                return str(session_id) if session_id else None
                
        except Exception as e:
            logger.error(f"Failed to get session ID for agent {agent_id}: {e}")
            return None
    
    async def store_message(
        self, 
        agent_id: str, 
        role: str, 
        content: str, 
        session_id: Optional[str] = None,
        tokens_used: int = 0,
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Store a message in the conversation history.
        
        Args:
            agent_id: The Letta agent ID
            role: Message role ('user' or 'assistant')
            content: Message content
            session_id: Optional session ID (will get or create if None)
            tokens_used: Number of tokens used
            model_name: LLM model name
            metadata: Additional metadata
            
        Returns:
            The message ID or None if failed
        """
        try:
            if not self.pool:
                await self.initialize()
            
            # Get or create session
            if not session_id:
                session_id = await self.get_session_id(agent_id)
                if not session_id:
                    session_id = await self.create_session(agent_id)
            
            session_uuid = UUID(session_id)
            
            async with self.pool.acquire() as conn:
                # Use the stored function to add memory
                import json
                memory_id = await conn.fetchval(
                    "SELECT add_agent_memory($1, $2, $3, $4, $5, $6)",
                    session_uuid,
                    role,
                    content,
                    tokens_used,
                    model_name,
                    json.dumps(metadata or {})
                )
                
                logger.debug(f"Stored message {memory_id} for agent {agent_id}, role: {role}")
                return str(memory_id)
                
        except Exception as e:
            logger.error(f"Failed to store message for agent {agent_id}: {e}")
            return None
    
    async def get_or_create_session(self, agent_id: str, task_id: Optional[str] = None) -> str:
        """Get existing active session or create a new one.
        
        Args:
            agent_id: The Letta agent ID
            task_id: Optional task ID
            
        Returns:
            The session ID
        """
        session_id = await self.get_session_id(agent_id)
        if not session_id:
            session_id = await self.create_session(agent_id, task_id)
        return session_id
    
    async def get_conversation_history(self, agent_id: str, limit: int = 50) -> List[LettaMessage]:
        """Get conversation history for an agent from our custom storage.
        
        Args:
            agent_id: The Letta agent ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of LettaMessage objects
        """
        try:
            if not self.pool:
                await self.initialize()
            
            # Extract UUID from agent_id to match what's stored in database
            agent_uuid = self._extract_uuid_from_agent_id(agent_id)
            
            async with self.pool.acquire() as conn:
                # Query directly by agent_id across all sessions
                rows = await conn.fetch(
                    """
                    SELECT 
                        m.memory_id,
                        m.role,
                        m.content,
                        m.timestamp,
                        m.tokens_used,
                        m.model_name,
                        m.metadata
                    FROM agent_memory m
                    JOIN agent_sessions s ON m.session_id = s.session_id
                    WHERE s.agent_id = $1 
                    ORDER BY m.timestamp ASC
                    LIMIT $2
                    """,
                    agent_uuid,
                    limit
                )
                
                messages = []
                for row in rows:
                    # Parse JSON metadata if it's a string
                    metadata = row['metadata'] or {}
                    if isinstance(metadata, str):
                        import json
                        try:
                            metadata = json.loads(metadata)
                        except (json.JSONDecodeError, TypeError):
                            metadata = {}
                    
                    messages.append(
                        LettaMessage(
                            id=str(row['memory_id']),
                            agent_id=agent_id,
                            role=row['role'],
                            content=row['content'],
                            timestamp=row['timestamp'],
                            metadata=metadata
                        )
                    )
                
                logger.debug(f"Retrieved {len(messages)} messages for agent {agent_id}")
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get conversation history for agent {agent_id}: {e}")
            return []
    
    async def end_session(self, agent_id: str, final_state: Optional[Dict[str, Any]] = None) -> bool:
        """End the active session for an agent.
        
        Args:
            agent_id: The Letta agent ID
            final_state: Optional final state to store
            
        Returns:
            True if session was ended, False otherwise
        """
        try:
            if not self.pool:
                await self.initialize()
            
            session_id = await self.get_session_id(agent_id)
            if not session_id:
                return False
            
            session_uuid = UUID(session_id)
            
            async with self.pool.acquire() as conn:
                # Use the stored function to end session
                import json
                success = await conn.fetchval(
                    "SELECT end_agent_session($1, $2)",
                    session_uuid,
                    json.dumps(final_state or {})
                )
                
                logger.info(f"Ended session {session_id} for agent {agent_id}")
                return bool(success)
                
        except Exception as e:
            logger.error(f"Failed to end session for agent {agent_id}: {e}")
            return False
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if a string is a valid UUID."""
        try:
            UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    def _extract_uuid_from_agent_id(self, agent_id: str) -> UUID:
        """Extract UUID from Letta agent ID (handles 'agent-' prefix)."""
        try:
            # If it starts with 'agent-', strip the prefix
            if agent_id.startswith('agent-'):
                uuid_part = agent_id[6:]  # Remove 'agent-' prefix
                return UUID(uuid_part)
            # If it's already a valid UUID, use it directly
            elif self._is_valid_uuid(agent_id):
                return UUID(agent_id)
            else:
                # Generate a consistent UUID based on the agent_id string
                import hashlib
                hash_obj = hashlib.md5(agent_id.encode())
                return UUID(hash_obj.hexdigest())
        except (ValueError, TypeError):
            # Fallback to generating a consistent UUID
            import hashlib
            hash_obj = hashlib.md5(agent_id.encode())
            return UUID(hash_obj.hexdigest())


# Singleton instance
conversation_persistence = LettaConversationPersistence()