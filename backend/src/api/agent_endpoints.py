"""
ATLAS Agent API Endpoints
Real agent integration for Tasks tab frontend communication
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import logging

try:
    import mlflow
    from mlflow.tracking import MlflowClient
except ImportError:
    mlflow = None
    MlflowClient = None

from ..agents.global_supervisor import GlobalSupervisorAgent
from ..agents.library import LibraryAgent
from ..agents.base import Task, TaskResult, AgentStatus
from ..agui.handlers import AGUIEventBroadcaster
from ..mlflow.enhanced_tracking import EnhancedATLASTracker
from ..mlflow.chat_tracking import chat_tracker
from ..database.chat_manager import chat_manager

logger = logging.getLogger(__name__)

# Request/Response Models
class TaskCreateRequest(BaseModel):
    task_type: str
    description: str
    priority: str = "medium"
    context: Optional[Dict[str, Any]] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    current_phase: str
    agents_active: List[str]
    estimated_completion: Optional[str]
    results: Optional[Dict[str, Any]] = None

class AgentInputRequest(BaseModel):
    message: str
    agent_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

# Global agent instances (in production, this would be managed differently)
active_agents: Dict[str, Any] = {}
active_tasks: Dict[str, Any] = {}

# Dependency to get AG-UI broadcaster
def get_agui_broadcaster(request: Request) -> AGUIEventBroadcaster:
    """Dependency to get AG-UI broadcaster from app state."""
    broadcaster = getattr(request.app.state, 'agui_broadcaster', None)
    if broadcaster:
        return broadcaster
    else:
        # Fallback broadcaster without connection manager
        return AGUIEventBroadcaster()

# Dependency removed - tracking now integrated into agents directly

# Create router
router = APIRouter(tags=["agents"])

@router.post("/tasks", response_model=Dict[str, Any])
async def create_agent_task(
    request: TaskCreateRequest,
    broadcaster: AGUIEventBroadcaster = Depends(get_agui_broadcaster)
):
    """Create a new task and assign it to the Global Supervisor agent."""
    try:
        # Generate unique task ID
        task_id = f"task_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Initialize enhanced MLflow tracking
        mlflow_tracker = EnhancedATLASTracker()
        logger.info(f"MLflow tracking available for task {task_id}")
        
        # Create chat session for this task
        chat_session_id = await chat_manager.get_or_create_session(
            task_id=task_id,
            user_id="default_user"
        )
        
        # Create MLflow chat experiment
        mlflow_run_id = await chat_tracker.create_chat_experiment(
            session_id=chat_session_id,
            task_id=task_id,
            chat_metadata={
                "task_type": request.task_type,
                "description": request.description,
                "priority": request.priority,
                "context": request.context or {}
            }
        )
        
        # Update chat session with MLflow run ID
        if mlflow_run_id:
            await chat_manager.update_session_mlflow_run(chat_session_id, mlflow_run_id)
        
        # Create task object
        task = Task(
            task_id=task_id,
            task_type=request.task_type,
            description=request.description,
            priority=request.priority,
            context=request.context or {}
        )
        
        # Initialize Global Supervisor for this task with MLflow tracker
        global_supervisor = GlobalSupervisorAgent(
            task_id=task_id,
            agui_broadcaster=broadcaster,
            mlflow_tracker=mlflow_tracker
        )
        
        # Initialize Library Agent (shared across tasks)
        library_agent_id = "library_agent_shared"
        if library_agent_id not in active_agents:
            library_agent = LibraryAgent(
                task_id=task_id,
                agui_broadcaster=broadcaster,
                mlflow_tracker=mlflow_tracker
            )
            active_agents[library_agent_id] = library_agent
            logger.info(f"Initialized shared Library Agent: {library_agent_id}")
        
        # Store active agents for this task
        active_agents[task_id] = {
            "global_supervisor": global_supervisor,
            "library_agent": active_agents[library_agent_id],
            "task": task,
            "created_at": datetime.now(),
            "status": "created",
            "mlflow_tracker": mlflow_tracker,
            "mlflow_run_id": mlflow_run_id,
            "chat_session_id": chat_session_id
        }
        
        # Broadcast task creation
        await broadcaster.broadcast_task_created(
            task_id=task_id,
            task_type=request.task_type,
            description=request.description,
            priority=request.priority
        )
        
        # Broadcast initial agent status
        await broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="global_supervisor",
            old_status="inactive",
            new_status="idle"
        )
        
        logger.info(f"Created task {task_id} with Global Supervisor and Library Agent")
        
        return {
            "task_id": task_id,
            "status": "created",
            "message": "Task created and assigned to Global Supervisor",
            "agents_initialized": ["global_supervisor", "library_agent"],
            "websocket_url": f"/api/agui/ws/{task_id}",
            "sse_url": f"/api/agui/stream/{task_id}",
            "mlflow_run_id": mlflow_tracker.current_run_id if mlflow_tracker else None,
            "mlflow_url": mlflow_tracker.get_current_run_url() if mlflow_tracker else None
        }
        
    except Exception as e:
        logger.error(f"Failed to create agent task: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")

@router.post("/tasks/{task_id}/start")
async def start_agent_task(
    task_id: str,
    broadcaster: AGUIEventBroadcaster = Depends(get_agui_broadcaster)
):
    """Start processing a created task with the Global Supervisor."""
    try:
        if task_id not in active_agents:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        task_data = active_agents[task_id]
        global_supervisor = task_data["global_supervisor"]
        task = task_data["task"]
        
        # Update task status
        task_data["status"] = "running"
        task_data["started_at"] = datetime.now()
        
        # Save initial user message to chat history
        chat_session_id = task_data.get("chat_session_id")
        if chat_session_id:
            await chat_manager.save_message(
                session_id=chat_session_id,
                message_type="user",
                content=task.description,
                metadata={"task_start": True, "task_type": task.task_type}
            )
        
        # Broadcast task start
        await broadcaster.broadcast_task_started(
            task_id=task_id,
            initial_prompt=task.description,
            teams_involved=["global_supervisor", "library_agent"]
        )
        
        # Start task processing asynchronously
        asyncio.create_task(_process_task_async(
            global_supervisor, task, task_id, broadcaster, chat_session_id
        ))
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Task processing initiated with Global Supervisor"
        }
        
    except Exception as e:
        logger.error(f"Failed to start task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Task start failed: {str(e)}")

async def _process_task_async(
    global_supervisor: GlobalSupervisorAgent,
    task: Task,
    task_id: str,
    broadcaster: AGUIEventBroadcaster,
    chat_session_id: Optional[str] = None
):
    """Process task asynchronously with the Global Supervisor."""
    try:
        logger.info(f"Starting async processing for task {task_id}")
        
        # Process the task
        start_time = time.time()
        result = await global_supervisor.process_task(task)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Update task status
        active_agents[task_id]["status"] = "completed" if result.success else "failed"
        active_agents[task_id]["completed_at"] = datetime.now()
        active_agents[task_id]["result"] = result
        
        # Save agent response to chat history
        if chat_session_id and result.content:
            message_id = await chat_manager.save_message(
                session_id=chat_session_id,
                message_type="agent",
                content=str(result.content),
                agent_id="global_supervisor",
                metadata={
                    "task_completion": True,
                    "success": result.success,
                    "processing_time_ms": processing_time_ms
                },
                processing_time_ms=processing_time_ms,
                model_used="claude-3-5-haiku-20241022"  # This would come from agent
            )
            
            # Track message in MLflow
            await chat_tracker.track_message(chat_session_id, {
                "message_type": "agent",
                "content": str(result.content),
                "agent_id": "global_supervisor",
                "processing_time_ms": processing_time_ms,
                "tokens_used": 0,  # This would come from the actual LLM call
                "cost_usd": 0.0,   # This would be calculated
                "model_used": "claude-3-5-haiku-20241022"
            })
        
        # Broadcast the actual agent response content
        logger.info(f"Task result - Success: {result.success}, Content length: {len(str(result.content)) if result.content else 0}")
        
        if result.success and result.content:
            logger.info(f"Broadcasting dialogue update for task {task_id}")
            try:
                # Broadcast the agent's detailed response
                await broadcaster.broadcast_dialogue_update(
                    task_id=task_id,
                    agent_id="global_supervisor",
                    message_id=f"response_{int(time.time())}",
                    direction="output",
                    content={
                        "type": "text",
                        "data": str(result.content)
                    },
                    sender="global_supervisor"
                )
                logger.info(f"Successfully broadcasted dialogue update for task {task_id}")
            except Exception as e:
                logger.error(f"Failed to broadcast dialogue update: {e}")
            
            # Then broadcast task completion
            await broadcaster.broadcast_task_completed(
                task_id=task_id,
                agent_id="global_supervisor",
                result_summary=str(result.content)[:200]
            )
        else:
            await broadcaster.broadcast_task_failed(
                task_id=task_id,
                agent_id="global_supervisor",
                error_message="; ".join(result.errors) if result.errors else "Unknown error"
            )
        
        logger.info(f"Completed async processing for task {task_id}: {result.success}")
        
    except Exception as e:
        logger.error(f"Error in async task processing for {task_id}: {e}")
        
        # Update task status and broadcast error
        active_agents[task_id]["status"] = "error"
        active_agents[task_id]["error"] = str(e)
        
        await broadcaster.broadcast_task_failed(
            task_id=task_id,
            agent_id="global_supervisor",
            error_message=str(e)
        )

@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_agent_task_status(task_id: str):
    """Get detailed status of an agent task."""
    try:
        if task_id not in active_agents:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        task_data = active_agents[task_id]
        task = task_data["task"]
        
        # Calculate progress based on agent status
        progress = 0.0
        current_phase = "created"
        agents_active = []
        
        if task_data["status"] == "running":
            progress = 45.0  # Placeholder progress calculation
            current_phase = "processing"
            agents_active = ["global_supervisor"]
        elif task_data["status"] == "completed":
            progress = 100.0
            current_phase = "completed"
        elif task_data["status"] == "failed" or task_data["status"] == "error":
            current_phase = "error"
        
        # Estimate completion time
        estimated_completion = None
        if task_data["status"] == "running":
            # Rough estimate: 2 minutes from start
            start_time = task_data.get("started_at")
            if start_time:
                import datetime as dt
                estimated_completion = (start_time + dt.timedelta(minutes=2)).isoformat()
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task_data["status"],
            progress=progress,
            current_phase=current_phase,
            agents_active=agents_active,
            estimated_completion=estimated_completion,
            results=task_data.get("result").__dict__ if task_data.get("result") else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.post("/tasks/{task_id}/input")
async def send_user_input(
    task_id: str,
    request: AgentInputRequest,
    broadcaster: AGUIEventBroadcaster = Depends(get_agui_broadcaster)
):
    """Send user input to a specific agent in a task."""
    try:
        if task_id not in active_agents:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        task_data = active_agents[task_id]
        target_agent_id = request.agent_id or "global_supervisor"
        
        # Broadcast user input received
        await broadcaster.broadcast_user_input_received(
            task_id=task_id,
            agent_id=target_agent_id,
            input_text=request.message,
            context=request.context
        )
        
        # Broadcast dialogue update showing user input
        await broadcaster.broadcast_dialogue_update(
            task_id=task_id,
            agent_id=target_agent_id,
            message_id=str(uuid.uuid4()),
            direction="input",
            content={
                "type": "text",
                "data": request.message
            },
            sender="user"
        )
        
        # Process the user input with the agent to capture metrics
        try:
            if target_agent_id == "global_supervisor" and "global_supervisor" in task_data:
                agent = task_data["global_supervisor"]
                
                # Use the agent's CallModel to process the user input
                system_prompt = await agent.get_system_prompt()
                
                response = await agent.call_model.call_model(
                    model_name="claude-3-5-haiku-20241022",
                    system_prompt=system_prompt,
                    most_recent_message=request.message,
                    max_tokens=500,
                    temperature=0.7
                )
                
                # Log conversation turn if we have enhanced tracker
                if hasattr(agent.mlflow_tracker, 'log_conversation_turn') and response.success:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        agent.mlflow_tracker.log_conversation_turn,
                        str(uuid.uuid4()),  # turn_id
                        agent.agent_id,     # agent_id
                        request.message,    # user_message
                        response.content,   # agent_response
                        1,                  # turn_number
                        request.context or {},  # context
                        response.response_time * 1000 if response.response_time else 0.0,  # response_time_ms
                        None,               # user_satisfaction
                        {"frontend_input": True}  # metadata
                    )
                
                if response.success:
                    # Broadcast the agent's response
                    await broadcaster.broadcast_dialogue_update(
                        task_id=task_id,
                        agent_id=target_agent_id,
                        message_id=str(uuid.uuid4()),
                        direction="output",
                        content={
                            "type": "text",
                            "data": response.content
                        },
                        sender=target_agent_id
                    )
                    
                    return {
                        "task_id": task_id,
                        "agent_id": target_agent_id,
                        "status": "processed",
                        "message": f"User input processed by {target_agent_id}",
                        "response": response.content[:200] + "..." if len(response.content) > 200 else response.content
                    }
                else:
                    logger.error(f"Agent {target_agent_id} failed to process input: {response.error}")
                    return {
                        "task_id": task_id,
                        "agent_id": target_agent_id,
                        "status": "error",
                        "message": f"Failed to process input: {response.error}"
                    }
            else:
                # For other agents or if agent not found, just acknowledge
                return {
                    "task_id": task_id,
                    "agent_id": target_agent_id,
                    "status": "received",
                    "message": f"User input forwarded to {target_agent_id}"
                }
                
        except Exception as e:
            logger.error(f"Error processing user input with agent {target_agent_id}: {e}")
            return {
                "task_id": task_id,
                "agent_id": target_agent_id,
                "status": "error",
                "message": f"Error processing input: {str(e)}"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send user input to task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Input forwarding failed: {str(e)}")

@router.get("/tasks/{task_id}/agents")
async def get_task_agents(task_id: str):
    """Get all agents associated with a task and their current status."""
    try:
        if task_id not in active_agents:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        task_data = active_agents[task_id]
        
        # Get agent statuses
        agents_info = {}
        
        # Global Supervisor
        if "global_supervisor" in task_data:
            supervisor = task_data["global_supervisor"]
            agents_info["global_supervisor"] = {
                "agent_id": supervisor.agent_id,
                "agent_type": supervisor.agent_type,
                "status": supervisor.status.value,
                "created_at": supervisor.created_at.isoformat(),
                "team_name": getattr(supervisor, 'team_name', 'ATLAS_Global')
            }
        
        # Library Agent
        if "library_agent" in task_data:
            library = task_data["library_agent"]
            agents_info["library_agent"] = {
                "agent_id": library.agent_id,
                "agent_type": library.agent_type,
                "status": library.status.value,
                "created_at": library.created_at.isoformat(),
                "stats": getattr(library, 'stats', {})
            }
        
        return {
            "task_id": task_id,
            "total_agents": len(agents_info),
            "agents": agents_info,
            "task_status": task_data["status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agents for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Agent retrieval failed: {str(e)}")

@router.get("/library/stats")
async def get_library_stats():
    """Get Library Agent statistics and health information."""
    try:
        # Find the shared library agent
        library_agent = active_agents.get("library_agent_shared")
        
        if not library_agent:
            return {
                "status": "not_initialized",
                "message": "Library Agent not yet initialized"
            }
        
        # Get stats from Library Agent
        stats = getattr(library_agent, 'stats', {})
        knowledge_store = getattr(library_agent, 'knowledge_store', {})
        
        return {
            "status": "operational",
            "agent_id": library_agent.agent_id,
            "current_status": library_agent.status.value,
            "stats": stats,
            "storage_summary": {
                category: len(items) for category, items in knowledge_store.items()
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get library stats: {e}")
        raise HTTPException(status_code=500, detail=f"Library stats retrieval failed: {str(e)}")

@router.post("/library/operation")
async def library_operation(
    operation_data: Dict[str, Any],
    broadcaster: AGUIEventBroadcaster = Depends(get_agui_broadcaster)
):
    """Perform a direct operation with the Library Agent."""
    try:
        # Find the shared library agent
        library_agent = active_agents.get("library_agent_shared")
        
        if not library_agent:
            raise HTTPException(status_code=404, detail="Library Agent not initialized")
        
        # Extract operation parameters
        operation = operation_data.get("operation", "search")
        query = operation_data.get("query")
        data = operation_data.get("data")
        context = operation_data.get("context", {})
        
        # Create a library task
        library_task = Task(
            task_id=f"lib_op_{int(time.time())}",
            task_type=f"library_{operation}",
            description=f"Direct library operation: {operation}",
            context={
                "operation": operation,
                "query": query,
                "data": data,
                "context": context
            }
        )
        
        # Process the library operation
        result = await library_agent.process_task(library_task)
        
        return {
            "operation": operation,
            "success": result.success,
            "result": result.content,
            "processing_time": result.processing_time,
            "errors": result.errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform library operation: {e}")
        raise HTTPException(status_code=500, detail=f"Library operation failed: {str(e)}")

# Cleanup endpoint for development
@router.delete("/tasks/{task_id}")
async def cleanup_task(task_id: str):
    """Clean up a completed or failed task (development endpoint)."""
    try:
        if task_id not in active_agents:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        task_data = active_agents[task_id]
        
        # Clean up agents
        if "global_supervisor" in task_data:
            task_data["global_supervisor"].cleanup()
        
        # Remove from active tasks
        del active_agents[task_id]
        
        return {
            "task_id": task_id,
            "status": "cleaned_up",
            "message": "Task and associated agents cleaned up successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Task cleanup failed: {str(e)}")