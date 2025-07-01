# /Users/nicholaspate/Documents/ATLAS/backend/src/agui/events.py

from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime
import json

class AGUIEventType(Enum):
    """Enumeration of all AG-UI event types for ATLAS communication."""
    
    # Connection Events
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    PING = "ping"
    
    # Task Management Events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    TASK_STATUS_CHANGED = "task_status_changed"
    
    # Agent Events
    AGENT_CREATED = "agent_created"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_MESSAGE_SENT = "agent_message_sent"
    AGENT_MESSAGE_RECEIVED = "agent_message_received"
    AGENT_DIALOGUE_UPDATE = "agent_dialogue_update"
    AGENT_ERROR = "agent_error"
    AGENT_INTERRUPTED = "agent_interrupted"
    AGENT_COMPLETED = "agent_completed"
    
    # Multi-Modal Content Events
    CONTENT_GENERATED = "content_generated"
    CONTENT_TYPE_DETECTED = "content_type_detected"
    FILE_UPLOADED = "file_uploaded"
    FILE_PROCESSED = "file_processed"
    
    # User Interaction Events
    USER_INPUT_RECEIVED = "user_input_received"
    USER_FEEDBACK_RECEIVED = "user_feedback_received"
    USER_APPROVAL_REQUIRED = "user_approval_required"
    USER_APPROVAL_RECEIVED = "user_approval_received"
    
    # System Events
    SYSTEM_MESSAGE = "system_message"
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"
    
    # Performance Events
    PERFORMANCE_METRICS = "performance_metrics"
    COST_UPDATE = "cost_update"
    TOKEN_USAGE_UPDATE = "token_usage_update"

@dataclass
class AGUIEvent:
    """Represents a single AG-UI event with all necessary metadata."""
    
    event_type: AGUIEventType
    task_id: str
    data: Dict[str, Any]
    agent_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    event_id: Optional[str] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if self.event_id is None:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for JSON serialization."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "task_id": self.task_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
        
        if self.agent_id:
            result["agent_id"] = self.agent_id
        
        return result
    
    def to_json(self) -> str:
        """Convert the event to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AGUIEvent':
        """Create an AGUIEvent from a dictionary."""
        return cls(
            event_type=AGUIEventType(data["event_type"]),
            task_id=data["task_id"],
            data=data.get("data", {}),
            agent_id=data.get("agent_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            event_id=data.get("event_id")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AGUIEvent':
        """Create an AGUIEvent from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

# Event factory functions for common event types
class AGUIEventFactory:
    """Factory class for creating common AG-UI events."""
    
    @staticmethod
    def task_started(task_id: str, initial_prompt: str, teams_involved: list) -> AGUIEvent:
        """Create a task started event."""
        return AGUIEvent(
            event_type=AGUIEventType.TASK_STARTED,
            task_id=task_id,
            data={
                "initial_prompt": initial_prompt,
                "teams_involved": teams_involved,
                "started_at": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def agent_status_changed(task_id: str, agent_id: str, old_status: str, new_status: str) -> AGUIEvent:
        """Create an agent status changed event."""
        return AGUIEvent(
            event_type=AGUIEventType.AGENT_STATUS_CHANGED,
            task_id=task_id,
            agent_id=agent_id,
            data={
                "old_status": old_status,
                "new_status": new_status,
                "changed_at": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def agent_dialogue_update(task_id: str, agent_id: str, message_id: str, 
                             direction: str, content: Dict[str, Any], sender: str) -> AGUIEvent:
        """Create an agent dialogue update event."""
        return AGUIEvent(
            event_type=AGUIEventType.AGENT_DIALOGUE_UPDATE,
            task_id=task_id,
            agent_id=agent_id,
            data={
                "message_id": message_id,
                "direction": direction,
                "content": content,
                "sender": sender,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def content_generated(task_id: str, agent_id: str, content_type: str, 
                         content_size: int, processing_time: float) -> AGUIEvent:
        """Create a content generated event."""
        return AGUIEvent(
            event_type=AGUIEventType.CONTENT_GENERATED,
            task_id=task_id,
            agent_id=agent_id,
            data={
                "content_type": content_type,
                "content_size_bytes": content_size,
                "processing_time_ms": processing_time,
                "generated_at": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def task_progress_update(task_id: str, progress_percentage: float, 
                           current_phase: str, message: str) -> AGUIEvent:
        """Create a task progress update event."""
        return AGUIEvent(
            event_type=AGUIEventType.TASK_PROGRESS,
            task_id=task_id,
            data={
                "progress_percentage": progress_percentage,
                "current_phase": current_phase,
                "message": message,
                "updated_at": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def performance_metrics_update(task_id: str, agent_id: str, metrics: Dict[str, Any]) -> AGUIEvent:
        """Create a performance metrics update event."""
        return AGUIEvent(
            event_type=AGUIEventType.PERFORMANCE_METRICS,
            task_id=task_id,
            agent_id=agent_id,
            data={
                "metrics": metrics,
                "recorded_at": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def cost_update(task_id: str, agent_id: str, cost_usd: float, 
                   token_count: int, model_name: str) -> AGUIEvent:
        """Create a cost update event."""
        return AGUIEvent(
            event_type=AGUIEventType.COST_UPDATE,
            task_id=task_id,
            agent_id=agent_id,
            data={
                "cost_usd": cost_usd,
                "token_count": token_count,
                "model_name": model_name,
                "updated_at": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def error_occurred(task_id: str, agent_id: str, error_type: str, 
                      error_message: str, traceback: str) -> AGUIEvent:
        """Create an error occurred event."""
        return AGUIEvent(
            event_type=AGUIEventType.ERROR_OCCURRED,
            task_id=task_id,
            agent_id=agent_id,
            data={
                "error_type": error_type,
                "error_message": error_message,
                "traceback": traceback,
                "occurred_at": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def user_approval_required(task_id: str, agent_id: str, approval_type: str, 
                              content: str, options: list) -> AGUIEvent:
        """Create a user approval required event."""
        return AGUIEvent(
            event_type=AGUIEventType.USER_APPROVAL_REQUIRED,
            task_id=task_id,
            agent_id=agent_id,
            data={
                "approval_type": approval_type,
                "content": content,
                "options": options,
                "requested_at": datetime.now().isoformat()
            }
        )