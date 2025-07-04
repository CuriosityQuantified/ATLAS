#!/usr/bin/env python3
"""
ATLAS Backend Startup Script
Properly initializes FastAPI with AG-UI and agent integration
"""

import sys
import os
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any
import logging
from dotenv import load_dotenv

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import AG-UI server components
from src.agui import create_agui_server, AGUIEventBroadcaster, AGUIEventFactory, AGUIServer
from src.api.agent_endpoints import router as agent_router
from src.mlflow.enhanced_tracking import EnhancedATLASTracker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
agui_server = None
mlflow_tracker = None
event_broadcaster = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global agui_server, mlflow_tracker, event_broadcaster
    
    logger.info("🚀 Starting ATLAS Backend Server")
    
    # Initialize MLflow tracker
    try:
        mlflow_tracker = EnhancedATLASTracker(
            tracking_uri="http://localhost:5002",
            enable_detailed_logging=True
        )
        logger.info("✅ MLflow Enhanced Tracker initialized")
    except Exception as e:
        logger.warning(f"⚠️ MLflow initialization failed: {e}")
        mlflow_tracker = None
    
    # Initialize AG-UI broadcaster
    event_broadcaster = AGUIEventBroadcaster(connection_manager=None)
    logger.info("✅ AG-UI Event Broadcaster initialized")
    
    # Initialize AG-UI server
    agui_server = create_agui_server()
    app.mount("/agui", agui_server)
    logger.info("✅ AG-UI Server mounted at /agui")
    
    # Set global instances for agent endpoints
    app.state.mlflow_tracker = mlflow_tracker
    app.state.event_broadcaster = event_broadcaster
    
    logger.info("✅ ATLAS Backend ready for connections")
    logger.info("📡 WebSocket endpoint: ws://localhost:8000/agui/ws")
    logger.info("📡 SSE endpoint: http://localhost:8000/agui/stream")
    logger.info("🌐 API endpoints: http://localhost:8000/api/agents/*")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down ATLAS Backend")
    if mlflow_tracker:
        try:
            mlflow_tracker.cleanup()
        except Exception as e:
            logger.error(f"Error during MLflow cleanup: {e}")

# Create FastAPI app
app = FastAPI(
    title="ATLAS Backend API",
    description="Multi-agent reasoning system with AG-UI support",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development frontend
        "http://localhost:3002",  # Current frontend port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include agent API routes
app.include_router(agent_router, prefix="/api/agents", tags=["agents"])

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint with system status."""
    return {
        "status": "online",
        "service": "ATLAS Backend",
        "version": "0.1.0",
        "ag_ui": {
            "websocket": "ws://localhost:8000/agui/ws",
            "sse": "http://localhost:8000/agui/stream",
            "status": "ready"
        },
        "agents": {
            "global_supervisor": "ready",
            "library_agent": "ready"
        },
        "mlflow": {
            "tracking_uri": "http://localhost:5002",
            "status": "connected" if mlflow_tracker else "disconnected"
        }
    }

# Health check for agents
@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "ag_ui": agui_server is not None,
            "mlflow": mlflow_tracker is not None,
            "event_broadcaster": event_broadcaster is not None
        }
    }

# Test AG-UI broadcasting
@app.post("/api/dev/test-broadcast")
async def test_broadcast(message: Dict[str, Any]):
    """Test AG-UI event broadcasting."""
    if not event_broadcaster:
        raise HTTPException(status_code=503, detail="Event broadcaster not initialized")
    
    try:
        await event_broadcaster.broadcast_event(
            event_type="test_broadcast",
            data=message
        )
        return {"status": "success", "message": "Event broadcast sent"}
    except Exception as e:
        logger.error(f"Broadcast test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Start the server
    uvicorn.run(
        "start_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )