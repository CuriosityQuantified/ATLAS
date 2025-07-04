"""
Chat Manager for ATLAS
Handles persistent storage and retrieval of chat conversations
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import asyncpg
from decimal import Decimal

from ..core.config import get_settings

settings = get_settings()

class ChatManager:
    """
    Manages chat session persistence and message storage
    Integrates with MLflow tracking for comprehensive conversation analytics
    """
    
    def __init__(self):
        self.connection_pool = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        if not self.connection_pool:
            self.connection_pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                min_size=2,
                max_size=10
            )
    
    async def close(self):
        """Close database connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
    
    async def create_chat_session(
        self, 
        task_id: str, 
        user_id: str = "default_user",
        mlflow_run_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new chat session linked to a task
        Returns the session UUID as string
        """
        await self.initialize()
        
        session_id = str(uuid4())
        session_metadata = metadata or {}
        
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_sessions (
                    id, task_id, user_id, mlflow_run_id, session_metadata, status
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, session_id, task_id, user_id, mlflow_run_id, json.dumps(session_metadata), 'active')
            
        return session_id
    
    async def get_or_create_session(
        self, 
        task_id: str, 
        user_id: str = "default_user",
        mlflow_run_id: Optional[str] = None
    ) -> str:
        """
        Get existing session for task_id or create new one
        Returns session UUID as string
        """
        await self.initialize()
        
        async with self.connection_pool.acquire() as conn:
            # Try to get existing session
            row = await conn.fetchrow("""
                SELECT id FROM chat_sessions 
                WHERE task_id = $1 AND user_id = $2
                ORDER BY created_at DESC
                LIMIT 1
            """, task_id, user_id)
            
            if row:
                return str(row['id'])
            else:
                # Create new session
                return await self.create_chat_session(task_id, user_id, mlflow_run_id)
    
    async def save_message(
        self,
        session_id: str,
        message_type: str,  # 'user', 'agent', 'system'
        content: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        processing_time_ms: int = 0,
        model_used: Optional[str] = None,
        response_quality: Optional[float] = None
    ) -> str:
        """
        Save a chat message to the database
        Returns message UUID as string
        """
        await self.initialize()
        
        message_id = str(uuid4())
        message_metadata = metadata or {}
        
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_messages (
                    id, session_id, message_type, content, agent_id, 
                    metadata, tokens_used, cost_usd, processing_time_ms,
                    model_used, response_quality
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, 
                message_id, session_id, message_type, content, agent_id,
                json.dumps(message_metadata), tokens_used, Decimal(str(cost_usd)), 
                processing_time_ms, model_used, response_quality
            )
            
        return message_id
    
    async def get_chat_history(
        self, 
        session_id: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Retrieve chat history for a session
        Returns list of message dictionaries
        """
        await self.initialize()
        
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, message_type, content, agent_id, timestamp,
                    metadata, tokens_used, cost_usd, processing_time_ms,
                    model_used, response_quality
                FROM chat_messages 
                WHERE session_id = $1
                ORDER BY timestamp ASC
                LIMIT $2 OFFSET $3
            """, session_id, limit, offset)
            
            messages = []
            for row in rows:
                message = {
                    'id': str(row['id']),
                    'message_type': row['message_type'],
                    'content': row['content'],
                    'agent_id': row['agent_id'],
                    'timestamp': row['timestamp'].isoformat(),
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'tokens_used': row['tokens_used'],
                    'cost_usd': float(row['cost_usd']) if row['cost_usd'] else 0.0,
                    'processing_time_ms': row['processing_time_ms'],
                    'model_used': row['model_used'],
                    'response_quality': float(row['response_quality']) if row['response_quality'] else None
                }
                messages.append(message)
                
            return messages
    
    async def get_chat_history_by_task(
        self, 
        task_id: str, 
        user_id: str = "default_user",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get chat history by task_id
        Returns list of message dictionaries
        """
        await self.initialize()
        
        async with self.connection_pool.acquire() as conn:
            # Get session ID for task
            session_row = await conn.fetchrow("""
                SELECT id FROM chat_sessions 
                WHERE task_id = $1 AND user_id = $2
                ORDER BY created_at DESC
                LIMIT 1
            """, task_id, user_id)
            
            if not session_row:
                return []
                
            session_id = str(session_row['id'])
            return await self.get_chat_history(session_id, limit)
    
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session information and statistics
        """
        await self.initialize()
        
        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    id, task_id, user_id, created_at, updated_at, status,
                    mlflow_run_id, session_metadata, message_count, 
                    total_tokens, total_cost_usd
                FROM chat_sessions 
                WHERE id = $1
            """, session_id)
            
            if not row:
                return None
                
            return {
                'id': str(row['id']),
                'task_id': row['task_id'],
                'user_id': row['user_id'],
                'created_at': row['created_at'].isoformat(),
                'updated_at': row['updated_at'].isoformat(),
                'status': row['status'],
                'mlflow_run_id': row['mlflow_run_id'],
                'metadata': json.loads(row['session_metadata']) if row['session_metadata'] else {},
                'message_count': row['message_count'],
                'total_tokens': row['total_tokens'],
                'total_cost_usd': float(row['total_cost_usd']) if row['total_cost_usd'] else 0.0
            }
    
    async def update_session_mlflow_run(self, session_id: str, mlflow_run_id: str):
        """
        Update session with MLflow run ID
        """
        await self.initialize()
        
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                UPDATE chat_sessions 
                SET mlflow_run_id = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, mlflow_run_id, session_id)
    
    async def close_session(self, session_id: str):
        """
        Mark session as closed/completed
        """
        await self.initialize()
        
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
                UPDATE chat_sessions 
                SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, session_id)
    
    async def get_recent_sessions(
        self, 
        user_id: str = "default_user", 
        limit: int = 20
    ) -> List[Dict]:
        """
        Get recent chat sessions for a user
        Returns session info with last message preview
        """
        await self.initialize()
        
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    cs.id, cs.task_id, cs.created_at, cs.status,
                    cs.message_count, cs.total_tokens, cs.total_cost_usd,
                    cm.content as last_message_content,
                    cm.timestamp as last_message_time,
                    cm.message_type as last_message_type
                FROM chat_sessions cs
                LEFT JOIN LATERAL (
                    SELECT content, timestamp, message_type
                    FROM chat_messages 
                    WHERE session_id = cs.id 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ) cm ON true
                WHERE cs.user_id = $1
                ORDER BY cs.updated_at DESC
                LIMIT $2
            """, user_id, limit)
            
            sessions = []
            for row in rows:
                session = {
                    'id': str(row['id']),
                    'task_id': row['task_id'],
                    'created_at': row['created_at'].isoformat(),
                    'status': row['status'],
                    'message_count': row['message_count'],
                    'total_tokens': row['total_tokens'],
                    'total_cost_usd': float(row['total_cost_usd']) if row['total_cost_usd'] else 0.0,
                    'last_message': {
                        'content': row['last_message_content'],
                        'timestamp': row['last_message_time'].isoformat() if row['last_message_time'] else None,
                        'type': row['last_message_type']
                    } if row['last_message_content'] else None
                }
                sessions.append(session)
                
            return sessions
    
    async def search_messages(
        self, 
        session_id: str, 
        search_term: str, 
        limit: int = 50
    ) -> List[Dict]:
        """
        Search messages within a session
        """
        await self.initialize()
        
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, message_type, content, agent_id, timestamp,
                    tokens_used, cost_usd, model_used
                FROM chat_messages 
                WHERE session_id = $1 AND content ILIKE $2
                ORDER BY timestamp DESC
                LIMIT $3
            """, session_id, f'%{search_term}%', limit)
            
            results = []
            for row in rows:
                result = {
                    'id': str(row['id']),
                    'message_type': row['message_type'],
                    'content': row['content'],
                    'agent_id': row['agent_id'],
                    'timestamp': row['timestamp'].isoformat(),
                    'tokens_used': row['tokens_used'],
                    'cost_usd': float(row['cost_usd']) if row['cost_usd'] else 0.0,
                    'model_used': row['model_used']
                }
                results.append(result)
                
            return results

# Global instance
chat_manager = ChatManager()