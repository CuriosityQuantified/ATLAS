# /Users/nicholaspate/Documents/ATLAS/backend/src/agui/server.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Dict, Set, Optional, AsyncGenerator
import uuid
from datetime import datetime
import logging

from .events import AGUIEvent, AGUIEventType
from .handlers import AGUIEventHandler

logger = logging.getLogger(__name__)

class AGUIConnectionManager:
    """Manages WebSocket connections and Server-Sent Events for AG-UI protocol."""
    
    def __init__(self):
        # WebSocket connections by task_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # SSE clients by task_id  
        self.sse_clients: Dict[str, Set[asyncio.Queue]] = {}
        # Event handler for processing AG-UI events
        self.event_handler = AGUIEventHandler()
        
    async def connect_websocket(self, websocket: WebSocket, task_id: str):
        """Connect a new WebSocket client for a specific task."""
        await websocket.accept()
        
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        
        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task {task_id}. Total connections: {len(self.active_connections[task_id])}")
        
        # Send initial connection event
        await self.broadcast_to_task(task_id, AGUIEvent(
            event_type=AGUIEventType.CONNECTION_ESTABLISHED,
            task_id=task_id,
            data={"connected_at": datetime.now().isoformat()}
        ))
    
    async def disconnect_websocket(self, websocket: WebSocket, task_id: str):
        """Disconnect a WebSocket client."""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
                
        logger.info(f"WebSocket disconnected for task {task_id}")
    
    def add_sse_client(self, task_id: str) -> asyncio.Queue:
        """Add a new SSE client and return its message queue."""
        if task_id not in self.sse_clients:
            self.sse_clients[task_id] = set()
        
        client_queue = asyncio.Queue()
        self.sse_clients[task_id].add(client_queue)
        
        logger.info(f"SSE client added for task {task_id}. Total SSE clients: {len(self.sse_clients[task_id])}")
        return client_queue
    
    def remove_sse_client(self, task_id: str, client_queue: asyncio.Queue):
        """Remove an SSE client."""
        if task_id in self.sse_clients:
            self.sse_clients[task_id].discard(client_queue)
            
            if not self.sse_clients[task_id]:
                del self.sse_clients[task_id]
    
    async def broadcast_to_task(self, task_id: str, event: AGUIEvent):
        """Broadcast an event to all clients listening to a specific task."""
        event_data = event.to_dict()
        
        # Broadcast to WebSocket connections
        if task_id in self.active_connections:
            disconnected_clients = set()
            
            for websocket in self.active_connections[task_id].copy():
                try:
                    await websocket.send_text(json.dumps(event_data))
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message: {e}")
                    disconnected_clients.add(websocket)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                await self.disconnect_websocket(client, task_id)
        
        # Broadcast to SSE connections
        if task_id in self.sse_clients:
            disconnected_queues = set()
            
            for client_queue in self.sse_clients[task_id].copy():
                try:
                    await client_queue.put(event_data)
                except Exception as e:
                    logger.warning(f"Failed to send SSE message: {e}")
                    disconnected_queues.add(client_queue)
            
            # Remove disconnected clients
            for queue in disconnected_queues:
                self.remove_sse_client(task_id, queue)
    
    async def broadcast_global(self, event: AGUIEvent):
        """Broadcast an event to all connected clients across all tasks."""
        for task_id in list(self.active_connections.keys()) + list(self.sse_clients.keys()):
            await self.broadcast_to_task(task_id, event)

class AGUIServer:
    """Main AG-UI server implementation for ATLAS real-time communication."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.connection_manager = AGUIConnectionManager()
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Configure CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Set up AG-UI protocol routes."""
        
        @self.app.websocket("/api/agui/ws/{task_id}")
        async def websocket_endpoint(websocket: WebSocket, task_id: str):
            """WebSocket endpoint for bidirectional real-time communication."""
            await self.connection_manager.connect_websocket(websocket, task_id)
            
            try:
                while True:
                    # Listen for messages from frontend
                    data = await websocket.receive_text()
                    
                    try:
                        message = json.loads(data)
                        await self._handle_frontend_message(task_id, message, websocket)
                    except json.JSONDecodeError:
                        await websocket.send_text(json.dumps({
                            "event_type": "error",
                            "data": {"message": "Invalid JSON format"}
                        }))
                        
            except WebSocketDisconnect:
                await self.connection_manager.disconnect_websocket(websocket, task_id)
            except Exception as e:
                logger.error(f"WebSocket error for task {task_id}: {e}")
                await self.connection_manager.disconnect_websocket(websocket, task_id)
        
        @self.app.get("/api/agui/stream/{task_id}")
        async def sse_endpoint(task_id: str):
            """Server-Sent Events endpoint for real-time updates."""
            return StreamingResponse(
                self._sse_generator(task_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        @self.app.post("/api/agui/broadcast/{task_id}")
        async def broadcast_to_task(task_id: str, event_data: dict):
            """HTTP endpoint to broadcast events to a specific task."""
            try:
                event = AGUIEvent(
                    event_type=AGUIEventType(event_data.get("event_type", "system_message")),
                    task_id=task_id,
                    data=event_data.get("data", {}),
                    agent_id=event_data.get("agent_id"),
                    timestamp=datetime.now()
                )
                
                await self.connection_manager.broadcast_to_task(task_id, event)
                return {"status": "success", "message": f"Event broadcasted to task {task_id}"}
                
            except Exception as e:
                logger.error(f"Failed to broadcast to task {task_id}: {e}")
                return {"status": "error", "message": str(e)}
        
        @self.app.post("/api/agui/broadcast")
        async def broadcast_global(event_data: dict):
            """HTTP endpoint to broadcast events to all connected clients."""
            try:
                event = AGUIEvent(
                    event_type=AGUIEventType(event_data.get("event_type", "system_message")),
                    task_id=event_data.get("task_id", "global"),
                    data=event_data.get("data", {}),
                    agent_id=event_data.get("agent_id"),
                    timestamp=datetime.now()
                )
                
                await self.connection_manager.broadcast_global(event)
                return {"status": "success", "message": "Event broadcasted globally"}
                
            except Exception as e:
                logger.error(f"Failed to broadcast globally: {e}")
                return {"status": "error", "message": str(e)}
    
    async def _sse_generator(self, task_id: str) -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events for a specific task."""
        client_queue = self.connection_manager.add_sse_client(task_id)
        
        try:
            # Send initial connection event
            initial_event = {
                "event_type": "connection_established",
                "task_id": task_id,
                "data": {"connected_at": datetime.now().isoformat()}
            }
            yield f"data: {json.dumps(initial_event)}\n\n"
            
            while True:
                # Wait for events in the queue
                try:
                    event_data = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    ping_event = {
                        "event_type": "ping",
                        "task_id": task_id,
                        "data": {"timestamp": datetime.now().isoformat()}
                    }
                    yield f"data: {json.dumps(ping_event)}\n\n"
                    
        except Exception as e:
            logger.error(f"SSE error for task {task_id}: {e}")
        finally:
            self.connection_manager.remove_sse_client(task_id, client_queue)
    
    async def _handle_frontend_message(self, task_id: str, message: dict, websocket: WebSocket):
        """Handle messages received from the frontend via WebSocket."""
        try:
            message_type = message.get("type", "unknown")
            
            if message_type == "user_input":
                # Handle user input for agents
                await self._process_user_input(task_id, message.get("data", {}), websocket)
            
            elif message_type == "agent_interrupt":
                # Handle agent interruption requests
                await self._process_agent_interrupt(task_id, message.get("agent_id"), websocket)
            
            elif message_type == "task_control":
                # Handle task control commands (pause, resume, cancel)
                await self._process_task_control(task_id, message.get("action"), websocket)
            
            else:
                # Echo unknown message types for debugging
                await websocket.send_text(json.dumps({
                    "event_type": "message_received",
                    "data": {"original_message": message, "status": "unknown_type"}
                }))
                
        except Exception as e:
            logger.error(f"Error handling frontend message: {e}")
            await websocket.send_text(json.dumps({
                "event_type": "error",
                "data": {"message": f"Failed to process message: {str(e)}"}
            }))
    
    async def _process_user_input(self, task_id: str, data: dict, websocket: WebSocket):
        """Process user input and forward to appropriate agent."""
        # This will be implemented when we integrate with actual agents
        response_event = AGUIEvent(
            event_type=AGUIEventType.USER_INPUT_RECEIVED,
            task_id=task_id,
            data={
                "input": data.get("input", ""),
                "target_agent": data.get("target_agent"),
                "processed_at": datetime.now().isoformat()
            }
        )
        
        await self.connection_manager.broadcast_to_task(task_id, response_event)
    
    async def _process_agent_interrupt(self, task_id: str, agent_id: Optional[str], websocket: WebSocket):
        """Process agent interruption request."""
        response_event = AGUIEvent(
            event_type=AGUIEventType.AGENT_INTERRUPTED,
            task_id=task_id,
            agent_id=agent_id,
            data={
                "interrupted_at": datetime.now().isoformat(),
                "status": "interrupt_requested"
            }
        )
        
        await self.connection_manager.broadcast_to_task(task_id, response_event)
    
    async def _process_task_control(self, task_id: str, action: str, websocket: WebSocket):
        """Process task control commands."""
        response_event = AGUIEvent(
            event_type=AGUIEventType.TASK_STATUS_CHANGED,
            task_id=task_id,
            data={
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "status": f"task_{action}"
            }
        )
        
        await self.connection_manager.broadcast_to_task(task_id, response_event)

# Factory function to create and configure AG-UI server
def create_agui_server() -> FastAPI:
    """Create a FastAPI app with AG-UI server configured."""
    app = FastAPI(
        title="ATLAS AG-UI Server",
        description="Real-time communication server for ATLAS multi-agent system",
        version="1.0.0"
    )
    
    # Initialize AG-UI server
    agui_server = AGUIServer(app)
    
    # Store reference to AG-UI server on app for later access
    app._agui_server = agui_server
    
    return app