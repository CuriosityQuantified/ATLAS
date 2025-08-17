"""API endpoints for Letta agent management."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
import time

from ..letta.service import letta_service
from ..letta.models import LettaAgent, LettaAgentConfig, LettaMessage, LettaConversation
from ..agui.events import AGUIEvent, AGUIEventType
from ..agui.handlers import AGUIEventBroadcaster


class MessageRequest(BaseModel):
    """Request model for sending messages."""
    message: str

router = APIRouter(prefix="/api/letta", tags=["letta"])


# Dependency to get AG-UI broadcaster
def get_agui_broadcaster(request: Request) -> Optional[AGUIEventBroadcaster]:
    """Dependency to get AG-UI broadcaster from app state."""
    return getattr(request.app.state, 'agui_broadcaster', None)


@router.post("/agents", response_model=LettaAgent)
async def create_agent(
    config: LettaAgentConfig,
    broadcaster: Optional[AGUIEventBroadcaster] = Depends(get_agui_broadcaster)
):
    """Create a new Letta agent."""
    try:
        agent = await letta_service.create_agent(config)
        
        # Broadcast agent creation event if broadcaster is available
        if broadcaster:
            await broadcaster.broadcast_agent_status(
                task_id="letta_ade",
                agent_id=agent.id,
                old_status="none",
                new_status=agent.status
            )
        
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=List[LettaAgent])
async def list_agents():
    """List all Letta agents."""
    try:
        return await letta_service.list_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}", response_model=LettaAgent)
async def get_agent(agent_id: str):
    """Get a specific agent by ID."""
    agent = await letta_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/agents/{agent_id}", response_model=LettaAgent)
async def update_agent(
    agent_id: str, 
    updates: dict = Body(...),
    broadcaster: Optional[AGUIEventBroadcaster] = Depends(get_agui_broadcaster)
):
    """Update an agent."""
    agent = await letta_service.update_agent(agent_id, updates)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Broadcast update event if broadcaster is available
    if broadcaster:
        await broadcaster.broadcast_agent_status(
            task_id="letta_ade",
            agent_id=agent.id,
            old_status="updating",
            new_status=agent.status
        )
    
    return agent


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    broadcaster: Optional[AGUIEventBroadcaster] = Depends(get_agui_broadcaster)
):
    """Delete an agent."""
    success = await letta_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Broadcast deletion event if broadcaster is available
    if broadcaster:
        await broadcaster.broadcast_agent_status(
            task_id="letta_ade",
            agent_id=agent_id,
            old_status="active",
            new_status="deleted"
        )
    
    return {"message": "Agent deleted successfully"}


@router.post("/agents/{agent_id}/messages", response_model=LettaMessage)
async def send_message(
    agent_id: str, 
    request: MessageRequest,
    broadcaster: Optional[AGUIEventBroadcaster] = Depends(get_agui_broadcaster)
):
    """Send a message to an agent."""
    # Broadcast user message event if broadcaster is available
    if broadcaster:
        await broadcaster.broadcast_dialogue_update(
            task_id=f"letta_chat_{agent_id}",
            agent_id=agent_id,
            message_id=f"user_{int(time.time())}",
            direction="input",
            content={
                "type": "text",
                "data": request.message
            },
            sender="user"
        )
    
    # Send message to agent
    response = await letta_service.send_message(agent_id, request.message)
    if not response:
        raise HTTPException(status_code=500, detail="Failed to get response from agent")
    
    # Broadcast agent response event if broadcaster is available
    if broadcaster:
        await broadcaster.broadcast_dialogue_update(
            task_id=f"letta_chat_{agent_id}",
            agent_id=agent_id,
            message_id=f"assistant_{int(time.time())}",
            direction="output",
            content={
                "type": "text",
                "data": response.content
            },
            sender="assistant"
        )
    
    return response


@router.get("/agents/{agent_id}/conversation", response_model=LettaConversation)
async def get_conversation(agent_id: str, limit: int = Query(50, le=200)):
    """Get conversation history for an agent."""
    return await letta_service.get_conversation_history(agent_id, limit)


@router.get("/agents/{agent_id}/stream")
async def stream_conversation(agent_id: str):
    """Stream conversation updates for an agent via SSE."""
    async def event_generator():
        """Generate SSE events for agent conversation."""
        task_id = f"letta_chat_{agent_id}"
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'agent_id': agent_id})}\n\n"
        
        # Subscribe to AG-UI events for this agent
        while True:
            try:
                # This is a placeholder - in production, you'd subscribe to actual events
                await asyncio.sleep(1)
                
                # Check for new messages or updates
                # This would be replaced with actual event subscription logic
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )