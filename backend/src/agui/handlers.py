# /Users/nicholaspate/Documents/ATLAS/backend/src/agui/handlers.py

import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from .events import AGUIEvent, AGUIEventType, AGUIEventFactory

logger = logging.getLogger(__name__)

# Type alias for event handler functions
EventHandler = Callable[[AGUIEvent], Awaitable[None]]

class AGUIEventHandler:
    """Handles processing and routing of AG-UI events within the ATLAS system."""
    
    def __init__(self):
        self.handlers: Dict[AGUIEventType, list[EventHandler]] = {}
        self.global_handlers: list[EventHandler] = []
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Set up default event handlers for common event types."""
        
        # Register default logging handlers
        self.register_handler(AGUIEventType.TASK_STARTED, self._log_task_started)
        self.register_handler(AGUIEventType.AGENT_STATUS_CHANGED, self._log_agent_status_change)
        self.register_handler(AGUIEventType.ERROR_OCCURRED, self._log_error)
        self.register_handler(AGUIEventType.PERFORMANCE_METRICS, self._log_performance_metrics)
        
        # Register MLflow integration handlers (when MLflow is available)
        self.register_handler(AGUIEventType.CONTENT_GENERATED, self._track_content_generation)
        self.register_handler(AGUIEventType.COST_UPDATE, self._track_cost_update)
        self.register_handler(AGUIEventType.AGENT_DIALOGUE_UPDATE, self._track_dialogue_update)
    
    def register_handler(self, event_type: AGUIEventType, handler: EventHandler):
        """Register an event handler for a specific event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type.value}")
    
    def register_global_handler(self, handler: EventHandler):
        """Register a handler that receives all events."""
        self.global_handlers.append(handler)
        logger.debug("Registered global event handler")
    
    async def process_event(self, event: AGUIEvent):
        """Process an event by calling all registered handlers."""
        try:
            # Call global handlers first
            for handler in self.global_handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Global handler error for event {event.event_id}: {e}")
            
            # Call specific handlers for the event type
            if event.event_type in self.handlers:
                for handler in self.handlers[event.event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Handler error for event {event.event_id} ({event.event_type.value}): {e}")
        
        except Exception as e:
            logger.error(f"Critical error processing event {event.event_id}: {e}")
    
    # Default event handlers
    
    async def _log_task_started(self, event: AGUIEvent):
        """Log task started events."""
        data = event.data
        logger.info(f"Task started: {event.task_id} with prompt: {data.get('initial_prompt', 'N/A')[:100]}...")
    
    async def _log_agent_status_change(self, event: AGUIEvent):
        """Log agent status changes."""
        data = event.data
        logger.info(f"Agent {event.agent_id} status changed from {data.get('old_status')} to {data.get('new_status')}")
    
    async def _log_error(self, event: AGUIEvent):
        """Log error events."""
        data = event.data
        logger.error(f"Error in task {event.task_id}, agent {event.agent_id}: {data.get('error_message')}")
    
    async def _log_performance_metrics(self, event: AGUIEvent):
        """Log performance metrics."""
        data = event.data
        metrics = data.get('metrics', {})
        logger.info(f"Performance metrics for {event.agent_id}: {metrics}")
    
    async def _track_content_generation(self, event: AGUIEvent):
        """Track content generation in MLflow (placeholder for future integration)."""
        data = event.data
        logger.debug(f"Content generated: {data.get('content_type')} "
                    f"({data.get('content_size_bytes')} bytes, "
                    f"{data.get('processing_time_ms')}ms)")
        
        # TODO: Integrate with MLflow tracking when agents are implemented
        # mlflow_tracker.log_multi_modal_content(...)
    
    async def _track_cost_update(self, event: AGUIEvent):
        """Track cost updates in MLflow (placeholder for future integration)."""
        data = event.data
        logger.debug(f"Cost update: ${data.get('cost_usd')} for {data.get('token_count')} tokens "
                    f"using {data.get('model_name')}")
        
        # TODO: Integrate with MLflow tracking when agents are implemented
        # mlflow_tracker.log_agent_transaction(...)
    
    async def _track_dialogue_update(self, event: AGUIEvent):
        """Track dialogue updates in MLflow (placeholder for future integration)."""
        data = event.data
        logger.debug(f"Dialogue update: {data.get('direction')} message from {data.get('sender')}")
        
        # TODO: Integrate with MLflow tracking when agents are implemented
        # mlflow_tracker.log_dialogue_message_stats(...)

class AGUIEventBroadcaster:
    """Utility class for broadcasting AG-UI events from agent code."""
    
    def __init__(self, connection_manager=None):
        self.connection_manager = connection_manager
        self.event_handler = AGUIEventHandler()
    
    async def broadcast_agent_status(self, task_id: str, agent_id: str, 
                                   old_status: str, new_status: str):
        """Broadcast agent status change."""
        event = AGUIEventFactory.agent_status_changed(task_id, agent_id, old_status, new_status)
        await self._broadcast_event(event)
    
    async def broadcast_dialogue_update(self, task_id: str, agent_id: str, 
                                      message_id: str, direction: str, 
                                      content: Dict[str, Any], sender: str):
        """Broadcast agent dialogue update."""
        event = AGUIEventFactory.agent_dialogue_update(
            task_id, agent_id, message_id, direction, content, sender
        )
        await self._broadcast_event(event)
    
    async def broadcast_content_generated(self, task_id: str, agent_id: str, 
                                        content_type: str, content_size: int, 
                                        processing_time: float):
        """Broadcast content generation event."""
        event = AGUIEventFactory.content_generated(
            task_id, agent_id, content_type, content_size, processing_time
        )
        await self._broadcast_event(event)
    
    async def broadcast_task_progress(self, task_id: str, progress_percentage: float, 
                                    current_phase: str, message: str):
        """Broadcast task progress update."""
        event = AGUIEventFactory.task_progress_update(
            task_id, progress_percentage, current_phase, message
        )
        await self._broadcast_event(event)
    
    async def broadcast_performance_metrics(self, task_id: str, agent_id: str, 
                                          metrics: Dict[str, Any]):
        """Broadcast performance metrics."""
        event = AGUIEventFactory.performance_metrics_update(task_id, agent_id, metrics)
        await self._broadcast_event(event)
    
    async def broadcast_cost_update(self, task_id: str, agent_id: str, 
                                  cost_usd: float, token_count: int, model_name: str):
        """Broadcast cost update."""
        event = AGUIEventFactory.cost_update(task_id, agent_id, cost_usd, token_count, model_name)
        await self._broadcast_event(event)
    
    async def broadcast_error(self, task_id: str, agent_id: str, 
                            error_type: str, error_message: str, traceback: str):
        """Broadcast error event."""
        event = AGUIEventFactory.error_occurred(
            task_id, agent_id, error_type, error_message, traceback
        )
        await self._broadcast_event(event)
    
    async def broadcast_user_approval_required(self, task_id: str, agent_id: str, 
                                             approval_type: str, content: str, options: list):
        """Broadcast user approval required event."""
        event = AGUIEventFactory.user_approval_required(
            task_id, agent_id, approval_type, content, options
        )
        await self._broadcast_event(event)
    
    async def _broadcast_event(self, event: AGUIEvent):
        """Internal method to broadcast an event."""
        # Process the event through handlers
        await self.event_handler.process_event(event)
        
        # Broadcast to connected clients if connection manager is available
        if self.connection_manager:
            await self.connection_manager.broadcast_to_task(event.task_id, event)
        else:
            logger.warning(f"No connection manager available to broadcast event {event.event_id}")

# Convenience functions for easy integration

async def broadcast_agent_message(task_id: str, agent_id: str, direction: str, 
                                content: Dict[str, Any], sender: str, 
                                broadcaster: Optional[AGUIEventBroadcaster] = None):
    """Convenience function to broadcast agent dialogue messages."""
    if not broadcaster:
        broadcaster = AGUIEventBroadcaster()
    
    message_id = f"{agent_id}_{datetime.now().timestamp()}"
    await broadcaster.broadcast_dialogue_update(
        task_id, agent_id, message_id, direction, content, sender
    )

async def broadcast_agent_status_change(task_id: str, agent_id: str, 
                                      old_status: str, new_status: str,
                                      broadcaster: Optional[AGUIEventBroadcaster] = None):
    """Convenience function to broadcast agent status changes."""
    if not broadcaster:
        broadcaster = AGUIEventBroadcaster()
    
    await broadcaster.broadcast_agent_status(task_id, agent_id, old_status, new_status)