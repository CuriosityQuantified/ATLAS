"""
API endpoints for thread management and interrupt handling.
This module provides FastAPI endpoints for managing LangGraph threads
and handling interrupt/resume patterns.
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any, Dict
from langgraph.types import Command
import uuid
import os

# Store the graph instance globally (will be set by the main application)
agent_graph = None

# Create FastAPI app
app = FastAPI(title="DeepAgents API", version="1.0.0")

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResumeRequest(BaseModel):
    """Request body for resuming an interrupted thread."""
    answer: str
    metadata: Optional[Dict[str, Any]] = None


class ThreadStateResponse(BaseModel):
    """Response model for thread state."""
    interrupted: bool
    pending_interrupt: Optional[Dict[str, Any]]
    messages: list
    thread_id: str


def set_agent_graph(graph):
    """
    Set the agent graph instance to be used by the API.
    This should be called by the main application after creating the graph.
    
    Args:
        graph: The LangGraph agent instance
    """
    global agent_graph
    agent_graph = graph


@app.post("/threads/{thread_id}/resume")
async def resume_thread(thread_id: str, request: ResumeRequest):
    """
    Resume an interrupted thread with the user's answer.
    
    Args:
        thread_id: The ID of the thread to resume
        request: The resume request containing the user's answer
    
    Returns:
        Status and result of the resume operation
    """
    if not agent_graph:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        # Resume the graph with the user's answer
        result = await agent_graph.ainvoke(
            Command(resume=request.answer),
            config={"thread_id": thread_id}
        )
        
        return {
            "status": "resumed",
            "thread_id": thread_id,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume thread: {str(e)}")


@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str) -> ThreadStateResponse:
    """
    Get the current state of a thread, including interrupt status.
    
    Args:
        thread_id: The ID of the thread to check
    
    Returns:
        Current state of the thread including interrupt information
    """
    if not agent_graph:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        # Get the current state of the thread
        state = await agent_graph.aget_state({"thread_id": thread_id})
        
        # Check for interrupt status
        interrupted = state.get("interrupted", False)
        pending_interrupt = state.get("pending_interrupt")
        messages = state.get("messages", [])
        
        return ThreadStateResponse(
            interrupted=interrupted,
            pending_interrupt=pending_interrupt,
            messages=messages,
            thread_id=thread_id
        )
    except Exception as e:
        # Thread might not exist yet
        return ThreadStateResponse(
            interrupted=False,
            pending_interrupt=None,
            messages=[],
            thread_id=thread_id
        )


@app.post("/threads")
async def create_thread():
    """
    Create a new thread for conversation.
    
    Returns:
        New thread ID
    """
    thread_id = str(uuid.uuid4())
    
    return {
        "thread_id": thread_id,
        "status": "created"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status of the API
    """
    return {
        "status": "healthy",
        "agent_initialized": agent_graph is not None,
        "interrupt_pattern_enabled": os.getenv("USE_INTERRUPT_PATTERN", "false").lower() == "true"
    }


# Optional: Add WebSocket support for real-time updates
from fastapi import WebSocket, WebSocketDisconnect
import json


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """
    WebSocket endpoint for real-time thread updates.
    
    Args:
        websocket: WebSocket connection
        thread_id: Thread ID to monitor
    """
    await websocket.accept()
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_state":
                # Send current thread state
                state = await get_thread_state(thread_id)
                await websocket.send_json(state.dict())
            
            elif message.get("type") == "resume":
                # Resume with answer
                answer = message.get("answer")
                if answer:
                    result = await resume_thread(
                        thread_id,
                        ResumeRequest(answer=answer)
                    )
                    await websocket.send_json(result)
                    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for thread {thread_id}")