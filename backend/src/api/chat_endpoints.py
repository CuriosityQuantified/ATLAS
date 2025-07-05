"""
Chat API Endpoints for ATLAS
Provides REST API for chat history management and persistence
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..database.chat_manager import chat_manager
from ..core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Pydantic models for request/response schemas

class ChatMessageCreate(BaseModel):
    message_type: str = Field(..., description="Type: user, agent, system")
    content: str = Field(..., description="Message content")
    agent_id: Optional[str] = Field(None, description="Agent ID for agent messages")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tokens_used: int = Field(0, description="Tokens used for this message")
    cost_usd: float = Field(0.0, description="Cost in USD for this message")
    processing_time_ms: int = Field(0, description="Processing time in milliseconds")
    model_used: Optional[str] = Field(None, description="Model used for generation")
    response_quality: Optional[float] = Field(None, description="Quality score 0.0-5.0")

class ChatMessageResponse(BaseModel):
    id: str
    message_type: str
    content: str
    agent_id: Optional[str]
    timestamp: str
    metadata: Dict[str, Any]
    tokens_used: int
    cost_usd: float
    processing_time_ms: int
    model_used: Optional[str]
    response_quality: Optional[float]

class ChatSessionCreate(BaseModel):
    task_id: str = Field(..., description="Task ID to link chat session")
    user_id: str = Field("default_user", description="User ID")
    mlflow_run_id: Optional[str] = Field(None, description="MLflow run ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatSessionResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    created_at: str
    updated_at: str
    status: str
    mlflow_run_id: Optional[str]
    metadata: Dict[str, Any]
    message_count: int
    total_tokens: int
    total_cost_usd: float

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]
    session_info: ChatSessionResponse

class RecentSessionResponse(BaseModel):
    id: str
    task_id: str
    created_at: str
    status: str
    message_count: int
    total_tokens: int
    total_cost_usd: float
    last_message: Optional[Dict[str, Any]]

# Chat Session Management Endpoints

@router.post("/sessions", response_model=Dict[str, str])
async def create_chat_session(session_data: ChatSessionCreate):
    """
    Create a new chat session linked to a task
    """
    try:
        session_id = await chat_manager.create_chat_session(
            task_id=session_data.task_id,
            user_id=session_data.user_id,
            mlflow_run_id=session_data.mlflow_run_id,
            metadata=session_data.metadata
        )
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str):
    """
    Get chat session information
    """
    try:
        session_info = await chat_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return ChatSessionResponse(**session_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat session: {str(e)}")

@router.get("/sessions/task/{task_id}", response_model=Dict[str, str])
async def get_or_create_session_for_task(
    task_id: str, 
    user_id: str = Query("default_user"),
    mlflow_run_id: Optional[str] = Query(None)
):
    """
    Get existing session for task or create new one
    """
    try:
        session_id = await chat_manager.get_or_create_session(
            task_id=task_id,
            user_id=user_id,
            mlflow_run_id=mlflow_run_id
        )
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get/create session: {str(e)}")

@router.put("/sessions/{session_id}/mlflow")
async def update_session_mlflow_run(session_id: str, mlflow_run_id: str):
    """
    Update session with MLflow run ID
    """
    try:
        await chat_manager.update_session_mlflow_run(session_id, mlflow_run_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update MLflow run ID: {str(e)}")

@router.put("/sessions/{session_id}/close")
async def close_chat_session(session_id: str):
    """
    Mark chat session as completed
    """
    try:
        await chat_manager.close_session(session_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close session: {str(e)}")

# Message Management Endpoints

@router.post("/sessions/{session_id}/messages", response_model=Dict[str, str])
async def save_chat_message(session_id: str, message_data: ChatMessageCreate):
    """
    Save a message to a chat session
    """
    try:
        message_id = await chat_manager.save_message(
            session_id=session_id,
            message_type=message_data.message_type,
            content=message_data.content,
            agent_id=message_data.agent_id,
            metadata=message_data.metadata,
            tokens_used=message_data.tokens_used,
            cost_usd=message_data.cost_usd,
            processing_time_ms=message_data.processing_time_ms,
            model_used=message_data.model_used,
            response_quality=message_data.response_quality
        )
        return {"message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get messages for a chat session
    """
    try:
        messages = await chat_manager.get_chat_history(session_id, limit, offset)
        return [ChatMessageResponse(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_complete_chat_history(session_id: str):
    """
    Get complete chat history with session info
    """
    try:
        # Get session info
        session_info = await chat_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Get messages
        messages = await chat_manager.get_chat_history(session_id)
        
        return ChatHistoryResponse(
            messages=[ChatMessageResponse(**msg) for msg in messages],
            session_info=ChatSessionResponse(**session_info)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

# Task-based endpoints for frontend integration

@router.get("/tasks/{task_id}/history", response_model=List[ChatMessageResponse])
async def get_chat_history_by_task(
    task_id: str, 
    user_id: str = Query("default_user"),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get chat history for a specific task
    This is the main endpoint the frontend will use
    """
    try:
        messages = await chat_manager.get_chat_history_by_task(task_id, user_id, limit)
        return [ChatMessageResponse(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task chat history: {str(e)}")

@router.post("/{task_id}/message")
async def send_chat_message(task_id: str, message_data: ChatMessageCreate):
    """
    Send a message and broadcast it immediately via WebSocket
    This endpoint handles both saving to DB and real-time broadcasting
    """
    try:
        from main import app
        
        # Get or create session for this task
        session_id = await chat_manager.get_or_create_session(
            task_id=task_id,
            user_id="default_user"
        )
        
        # Save message to database
        message_id = await chat_manager.save_message(
            session_id=session_id,
            message_type=message_data.message_type,
            content=message_data.content,
            agent_id=message_data.agent_id,
            metadata=message_data.metadata,
            tokens_used=message_data.tokens_used,
            cost_usd=message_data.cost_usd,
            processing_time_ms=message_data.processing_time_ms,
            model_used=message_data.model_used,
            response_quality=message_data.response_quality
        )
        
        # Broadcast via AG-UI if available
        broadcaster = getattr(app.state, 'agui_broadcaster', None)
        if broadcaster and message_data.message_type == 'user':
            # Broadcast user message as dialogue update
            await broadcaster.broadcast_dialogue_update(
                task_id=task_id,
                agent_id='user',
                message_id=message_id,
                direction='input',
                content={
                    'type': 'text',
                    'data': message_data.content
                },
                sender='user'
            )
        elif broadcaster and message_data.agent_id:
            # Broadcast agent message
            await broadcaster.broadcast_dialogue_update(
                task_id=task_id,
                agent_id=message_data.agent_id,
                message_id=message_id,
                direction='output',
                content={
                    'type': 'text',
                    'data': message_data.content
                },
                sender=message_data.agent_id
            )
        
        return {
            "message_id": message_id,
            "status": "success",
            "broadcast": broadcaster is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/recent", response_model=List[RecentSessionResponse])
async def get_recent_chat_sessions(
    user_id: str = Query("default_user"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get recent chat sessions for populating task dropdown
    """
    try:
        sessions = await chat_manager.get_recent_sessions(user_id, limit)
        return [RecentSessionResponse(**session) for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent sessions: {str(e)}")

# Search and utility endpoints

@router.get("/sessions/{session_id}/search", response_model=List[ChatMessageResponse])
async def search_chat_messages(
    session_id: str,
    q: str = Query(..., description="Search term"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search messages within a chat session
    """
    try:
        results = await chat_manager.search_messages(session_id, q, limit)
        return [ChatMessageResponse(**msg) for msg in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search messages: {str(e)}")

# Health and status endpoints

@router.get("/health")
async def chat_health_check():
    """
    Health check for chat system
    """
    try:
        # Try to initialize connection
        await chat_manager.initialize()
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Chat system unhealthy: {str(e)}")

@router.get("/stats")
async def get_chat_stats():
    """
    Get overall chat system statistics
    """
    try:
        await chat_manager.initialize()
        # Could add aggregate statistics here
        return {"status": "available", "features": ["persistence", "search", "mlflow_integration"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# Cleanup endpoint for development
@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete a chat session (development only)
    """
    try:
        await chat_manager.initialize()
        async with chat_manager.connection_pool.acquire() as conn:
            # Delete messages first (cascade should handle this)
            await conn.execute("DELETE FROM chat_sessions WHERE id = $1", session_id)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")