# /Users/nicholaspate/Documents/ATLAS/backend/src/agui/__init__.py

"""
ATLAS AG-UI (Agent-Generated User Interface) Module

This module provides real-time communication infrastructure for the ATLAS multi-agent system,
enabling bidirectional communication between the frontend dashboard and backend agents.

Key Components:
- AGUIServer: FastAPI-based server with WebSocket and SSE support
- AGUIEvent: Event system for structured communication
- AGUIEventHandler: Event processing and routing
- AGUIEventBroadcaster: Utility for broadcasting events from agent code

Usage Example:
    from backend.src.agui import create_agui_server, AGUIEventBroadcaster
    
    # Create AG-UI server
    app = create_agui_server()
    
    # Broadcast events from agent code
    broadcaster = AGUIEventBroadcaster()
    await broadcaster.broadcast_agent_status(task_id, agent_id, "idle", "active")
"""

from .server import AGUIServer, AGUIConnectionManager, create_agui_server
from .events import (
    AGUIEvent, 
    AGUIEventType, 
    AGUIEventFactory
)
from .handlers import (
    AGUIEventHandler, 
    AGUIEventBroadcaster,
    broadcast_agent_message,
    broadcast_agent_status_change
)

__all__ = [
    # Server components
    "AGUIServer",
    "AGUIConnectionManager", 
    "create_agui_server",
    
    # Event system
    "AGUIEvent",
    "AGUIEventType",
    "AGUIEventFactory",
    
    # Event handling
    "AGUIEventHandler",
    "AGUIEventBroadcaster",
    "broadcast_agent_message",
    "broadcast_agent_status_change",
]

# Version information
__version__ = "1.0.0"
__author__ = "ATLAS Development Team"