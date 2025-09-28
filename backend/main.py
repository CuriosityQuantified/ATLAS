"""
ATLAS Backend Entry Point
FastAPI server with AG-UI protocol support and real-time communication
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn
import os
import logging
from dotenv import load_dotenv

# Import AG-UI server components
from src.agui import create_agui_server, AGUIEventBroadcaster, AGUIEventFactory, AGUIServer
from src.agui.server import AGUIConnectionManager
from src.agui.copilot_bridge import setup_copilot_routes

# Import API endpoints
from src.api.agent_endpoints import router as agent_router
from src.api.chat_endpoints import router as chat_router
from src.api.letta_endpoints import router as letta_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting ATLAS backend server with AG-UI integration...")
    
    # Get reference to the AG-UI server (created by create_agui_server)
    # The server instance is stored on the app during creation
    agui_server = getattr(app, '_agui_server', None)
    if agui_server:
        app.state.agui_server = agui_server
        # Initialize AG-UI event broadcaster with connection manager
        app.state.agui_broadcaster = AGUIEventBroadcaster(agui_server.connection_manager)
        logger.info("AG-UI broadcaster initialized with connection manager")
    else:
        # Fallback without connection manager
        app.state.agui_broadcaster = AGUIEventBroadcaster()
        logger.warning("AG-UI broadcaster initialized without connection manager")
    
    # TODO: Initialize database connections
    # TODO: Initialize MLflow tracking
    # TODO: Initialize agent management system
    
    logger.info("ATLAS backend server started successfully")
    yield
    
    logger.info("Shutting down ATLAS backend server...")
    # Cleanup resources here
    logger.info("ATLAS backend server shut down complete")

# Create the main FastAPI application with AG-UI integration
app = create_agui_server()

# Store reference to the AG-UI server instance for access to connection manager
app.state.agui_server = None  # Will be set during app initialization

# Update app configuration
app.title = "ATLAS Backend API"
app.description = "Agentic Task Logic & Analysis System - Multi-Agent Backend with Real-time Communication"
app.version = "3.0.0"

# Update CORS configuration for broader development support
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative frontend port
        "http://127.0.0.1:3001",
        "http://localhost:3002",  # Current frontend port
        "http://127.0.0.1:3002",
        "http://localhost:8080"   # Legacy support
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add lifespan to the existing app
app.router.lifespan_context = lifespan

# Include API routers
app.include_router(agent_router, prefix="/api")
app.include_router(chat_router)
app.include_router(letta_router)

# Set up CopilotKit bridge
# Create a connection manager instance for CopilotKit
copilot_agui_manager = AGUIConnectionManager()
setup_copilot_routes(app, copilot_agui_manager)

@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "service": "ATLAS Backend API", 
        "version": app.version,
        "status": "running",
        "features": {
            "agui_protocol": "enabled",
            "real_time_communication": "enabled",
            "multi_agent_support": "enabled"
        },
        "endpoints": {
            "health": "/health",
            "api_docs": "/docs",
            "agui_websocket": "/api/agui/ws/{task_id}",
            "agui_sse": "/api/agui/stream/{task_id}",
            "tasks": "/api/tasks",
            "agents": "/api/agents"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with service status."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # This would be dynamic
        "services": {
            "agui_server": "running",
            "mlflow": "connected",  # TODO: Check actual MLflow status
            "database": "connected"  # TODO: Check actual database status
        }
    }

# Task Management Endpoints

@app.post("/api/tasks")
async def create_task(task_data: Dict[str, Any]):
    """Create a new ATLAS task."""
    try:
        task_id = f"task_{hash(str(task_data)) % 100000}"
        
        # TODO: Implement actual task creation logic
        # This is a placeholder implementation
        
        # Broadcast task creation event
        broadcaster = getattr(app.state, 'agui_broadcaster', None)
        if broadcaster:
            await broadcaster.broadcast_task_progress(
                task_id=task_id,
                progress_percentage=0.0,
                current_phase="initialization",
                message="Task created successfully"
            )
        
        return {
            "task_id": task_id,
            "status": "created",
            "message": "Task created and queued for execution",
            "websocket_url": f"/api/agui/ws/{task_id}",
            "sse_url": f"/api/agui/stream/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a specific task."""
    # TODO: Implement actual task status retrieval
    return {
        "task_id": task_id,
        "status": "running",
        "progress": 45.5,
        "current_phase": "analysis",
        "agents_active": 3,
        "estimated_completion": "2024-01-01T12:00:00Z"
    }

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running task."""
    try:
        # TODO: Implement actual task cancellation logic
        
        # Broadcast task cancellation event
        broadcaster = getattr(app.state, 'agui_broadcaster', None)
        if broadcaster:
            await broadcaster.broadcast_task_progress(
                task_id=task_id,
                progress_percentage=100.0,
                current_phase="cancelled",
                message="Task cancelled by user request"
            )
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancellation initiated"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Task cancellation failed: {str(e)}")

# Agent Management Endpoints

@app.get("/api/agents")
async def list_agents():
    """List all available agent types and their current status."""
    # TODO: Implement actual agent listing
    return {
        "global_supervisor": {"status": "ready", "type": "supervisor"},
        "research_team": {
            "supervisor": {"status": "ready", "type": "supervisor"},
            "workers": {
                "web_researcher": {"status": "idle", "type": "worker"},
                "data_analyst": {"status": "idle", "type": "worker"}
            }
        },
        "analysis_team": {
            "supervisor": {"status": "ready", "type": "supervisor"},
            "workers": {
                "swot_analyzer": {"status": "idle", "type": "worker"},
                "trend_analyzer": {"status": "idle", "type": "worker"}
            }
        },
        "writing_team": {
            "supervisor": {"status": "ready", "type": "supervisor"},
            "workers": {
                "content_writer": {"status": "idle", "type": "worker"},
                "editor": {"status": "idle", "type": "worker"}
            }
        },
        "rating_team": {
            "supervisor": {"status": "ready", "type": "supervisor"},
            "workers": {
                "quality_reviewer": {"status": "idle", "type": "worker"}
            }
        }
    }

# Development and Testing Endpoints

@app.get("/api/agui/broadcaster")
async def get_agui_broadcaster():
    """Get a reference to the shared AG-UI broadcaster for agents."""
    broadcaster = getattr(app.state, 'agui_broadcaster', None)
    if broadcaster:
        return {
            "status": "available",
            "has_connection_manager": broadcaster.connection_manager is not None,
            "message": "AG-UI broadcaster ready for agent integration"
        }
    else:
        raise HTTPException(status_code=500, detail="AG-UI broadcaster not initialized")

@app.post("/api/dev/simulate-agent-activity")
async def simulate_agent_activity(simulation_data: Dict[str, Any]):
    """Development endpoint to simulate agent activity for testing AG-UI."""
    try:
        task_id = simulation_data.get("task_id", "demo_task")
        agent_id = simulation_data.get("agent_id", "demo_agent")
        
        broadcaster = getattr(app.state, 'agui_broadcaster', None)
        if not broadcaster:
            raise HTTPException(status_code=500, detail="AG-UI broadcaster not available")
        
        # Simulate various agent activities
        await broadcaster.broadcast_agent_status(task_id, agent_id, "idle", "active")
        
        # Simulate dialogue update
        await broadcaster.broadcast_dialogue_update(
            task_id=task_id,
            agent_id=agent_id,
            message_id=f"sim_{task_id}_{agent_id}",
            direction="output",
            content={
                "type": "text",
                "data": "This is a simulated agent response for testing purposes."
            },
            sender=agent_id
        )
        
        # Simulate content generation
        await broadcaster.broadcast_content_generated(
            task_id=task_id,
            agent_id=agent_id,
            content_type="text",
            content_size=1024,
            processing_time=1500.0
        )
        
        return {
            "status": "success",
            "message": f"Simulated activity for agent {agent_id} in task {task_id}",
            "events_sent": 3
        }
        
    except Exception as e:
        logger.error(f"Failed to simulate agent activity: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

# Error Handlers

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource was not found",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True if os.getenv("PYTHON_ENV") == "development" else False,
        log_level="info"
    )