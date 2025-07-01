# /Users/nicholaspate/Documents/ATLAS/backend/src/agents/base.py

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging

from ..utils.call_model import CallModel
from ..agui.handlers import AGUIEventBroadcaster
from ..mlflow.tracking import ATLASMLflowTracker

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent status enumeration for tracking agent states."""
    IDLE = "idle"
    ACTIVE = "active" 
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"

@dataclass
class Task:
    """Task data structure for agent coordination."""
    task_id: str
    task_type: str
    description: str
    priority: str = "medium"
    assigned_to: Optional[str] = None
    parent_task_id: Optional[str] = None
    context: Dict[str, Any] = None
    deadline: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.context is None:
            self.context = {}

@dataclass
class TaskResult:
    """Task result data structure for agent responses."""
    task_id: str
    agent_id: str
    result_type: str
    content: Union[str, Dict[str, Any]]
    success: bool
    processing_time: float
    metadata: Dict[str, Any] = None
    errors: List[str] = None
    requires_review: bool = True
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.errors is None:
            self.errors = []

@dataclass
class ReviewSubmission:
    """Review submission for quality assurance."""
    submission_id: str
    task_result: TaskResult
    review_type: str  # "individual", "task", "general"
    submitted_to: Optional[str] = None  # specific reviewer or team
    submitted_at: datetime = None
    
    def __post_init__(self):
        if self.submitted_at is None:
            self.submitted_at = datetime.now()

class BaseAgent(ABC):
    """Base class for all ATLAS agents with CallModel integration and AG-UI broadcasting."""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        persona: str,
        task_id: Optional[str] = None,
        agui_broadcaster: Optional[AGUIEventBroadcaster] = None,
        mlflow_tracker: Optional[ATLASMLflowTracker] = None
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.persona = persona
        self.task_id = task_id or f"task_{int(time.time())}"
        self.status = AgentStatus.IDLE
        self.current_task: Optional[Task] = None
        self.task_history: List[Task] = []
        self.created_at = datetime.now()
        
        # Initialize tracking components
        self.agui_broadcaster = agui_broadcaster or AGUIEventBroadcaster(connection_manager=None)
        self.mlflow_tracker = mlflow_tracker or ATLASMLflowTracker()
        
        # Initialize CallModel with tracking integration
        self.call_model = CallModel(
            enable_threading=True,
            max_workers=3,
            task_id=self.task_id,
            agent_id=self.agent_id,
            agui_broadcaster=self.agui_broadcaster,
            mlflow_tracker=self.mlflow_tracker
        )
        
        logger.info(f"Initialized {self.agent_type} agent: {self.agent_id}")
    
    async def update_status(self, new_status: AgentStatus, context: Optional[str] = None):
        """Update agent status and broadcast change."""
        old_status = self.status.value
        self.status = new_status
        
        # Broadcast status change
        await self.agui_broadcaster.broadcast_agent_status(
            self.task_id, self.agent_id, old_status, new_status.value
        )
        
        logger.info(f"Agent {self.agent_id} status: {old_status} → {new_status.value}")
        if context:
            logger.debug(f"Status context: {context}")
    
    async def call_library(
        self, 
        operation: str, 
        query: Optional[str] = None, 
        data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call the Library agent for knowledge management operations.
        
        Args:
            operation: Type of operation ('search', 'add', 'modify', 'vector_query', 'graph_query', etc.)
            query: Search or query string
            data: Data to add or modify
            context: Additional context for the operation
        """
        # Import here to avoid circular imports
        from .library import LibraryAgent
        
        library_request = {
            "operation": operation,
            "query": query,
            "data": data,
            "context": context or {},
            "requesting_agent": self.agent_id,
            "task_id": self.task_id
        }
        
        # This will be implemented as a tool call to LibraryAgent
        # For now, return a placeholder response
        return {
            "status": "success",
            "operation": operation,
            "result": f"Library operation '{operation}' processed for agent {self.agent_id}",
            "metadata": {"timestamp": datetime.now().isoformat()}
        }
    
    async def submit_for_review(
        self, 
        task_result: TaskResult, 
        review_type: str = "general",
        specific_reviewer: Optional[str] = None
    ) -> ReviewSubmission:
        """Submit task result for quality review.
        
        Args:
            task_result: The completed task result
            review_type: Type of review needed ('individual', 'task', 'general')
            specific_reviewer: Specific reviewer agent ID if known
        """
        submission = ReviewSubmission(
            submission_id=str(uuid.uuid4()),
            task_result=task_result,
            review_type=review_type,
            submitted_to=specific_reviewer
        )
        
        # Broadcast review submission
        await self.agui_broadcaster.broadcast_dialogue_update(
            task_id=self.task_id,
            agent_id=self.agent_id,
            message_id=submission.submission_id,
            direction="output",
            content={
                "type": "review_submission",
                "data": {
                    "submission_id": submission.submission_id,
                    "review_type": review_type,
                    "submitted_to": specific_reviewer or "review_team",
                    "task_summary": task_result.content[:100] if isinstance(task_result.content, str) else "Complex task result"
                },
                "metadata": {
                    "timestamp": submission.submitted_at.isoformat(),
                    "requires_review": task_result.requires_review
                }
            },
            sender=self.agent_id
        )
        
        logger.info(f"Agent {self.agent_id} submitted task {task_result.task_id} for {review_type} review")
        return submission
    
    @abstractmethod
    async def process_task(self, task: Task) -> TaskResult:
        """Process a task and return results. Must be implemented by subclasses."""
        pass
    
    async def get_system_prompt(self) -> str:
        """Get the agent's system prompt including persona and current context."""
        base_prompt = f"""You are {self.agent_id}, a {self.agent_type} in the ATLAS multi-agent system.

PERSONA & RESPONSIBILITIES:
{self.persona}

CURRENT STATUS: {self.status.value}
TASK ID: {self.task_id}

CAPABILITIES:
- You can call the Library agent for knowledge management: call_library(operation, query, data, context)
- You can submit work for review: submit_for_review(task_result, review_type, specific_reviewer)
- You have access to multiple LLM providers through your CallModel interface

GUIDELINES:
- Always maintain your assigned persona and responsibilities
- Coordinate with other agents through proper channels
- Submit completed work for quality review when appropriate
- Use the Library agent for persistent knowledge management
- Provide clear, actionable results with proper context"""

        return base_prompt
    
    def cleanup(self):
        """Cleanup agent resources."""
        if self.call_model:
            self.call_model.cleanup()
        logger.info(f"Agent {self.agent_id} cleaned up successfully")

class BaseSupervisor(BaseAgent):
    """Base class for supervisor agents that manage teams of workers."""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        persona: str,
        team_name: str,
        worker_agent_ids: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(agent_id, agent_type, persona, **kwargs)
        self.team_name = team_name
        self.worker_agent_ids = worker_agent_ids or []
        self.worker_statuses: Dict[str, AgentStatus] = {}
        self.active_tasks: Dict[str, Task] = {}  # task_id -> Task
        self.task_assignments: Dict[str, str] = {}  # task_id -> worker_id
        
        # Initialize worker statuses
        for worker_id in self.worker_agent_ids:
            self.worker_statuses[worker_id] = AgentStatus.IDLE
    
    async def delegate_task(self, task: Task, worker_id: str) -> bool:
        """Delegate a task to a specific worker agent.
        
        Args:
            task: The task to delegate
            worker_id: ID of the worker agent to assign the task to
            
        Returns:
            bool: True if task was successfully delegated
        """
        if worker_id not in self.worker_agent_ids:
            logger.error(f"Worker {worker_id} not in team {self.team_name}")
            return False
        
        if worker_id in self.task_assignments.values():
            logger.warning(f"Worker {worker_id} already has an active task")
            # Could implement queuing here if needed
        
        # Record task assignment
        self.active_tasks[task.task_id] = task
        self.task_assignments[task.task_id] = worker_id
        task.assigned_to = worker_id
        
        # Update worker status
        self.worker_statuses[worker_id] = AgentStatus.ACTIVE
        
        # Broadcast task delegation
        await self.agui_broadcaster.broadcast_dialogue_update(
            task_id=self.task_id,
            agent_id=self.agent_id,
            message_id=str(uuid.uuid4()),
            direction="output",
            content={
                "type": "task_delegation",
                "data": {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "worker_id": worker_id,
                    "description": task.description,
                    "priority": task.priority
                },
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "team": self.team_name
                }
            },
            sender=self.agent_id
        )
        
        logger.info(f"Supervisor {self.agent_id} delegated task {task.task_id} to worker {worker_id}")
        return True
    
    async def monitor_workers(self) -> Dict[str, Any]:
        """Monitor worker agent statuses and return team summary.
        
        Returns:
            Dict containing team status summary
        """
        team_status = {
            "team_name": self.team_name,
            "supervisor_id": self.agent_id,
            "total_workers": len(self.worker_agent_ids),
            "worker_statuses": dict(self.worker_statuses),
            "active_tasks": len(self.active_tasks),
            "task_assignments": dict(self.task_assignments),
            "timestamp": datetime.now().isoformat()
        }
        
        # Count workers by status
        status_counts = {}
        for status in self.worker_statuses.values():
            status_counts[status.value] = status_counts.get(status.value, 0) + 1
        team_status["status_distribution"] = status_counts
        
        return team_status
    
    async def handle_review_notification(self, review_result: Dict[str, Any]) -> None:
        """Handle notification from review team about task completion.
        
        Args:
            review_result: Review results from the rating team
        """
        task_id = review_result.get("task_id")
        worker_id = self.task_assignments.get(task_id)
        approved = review_result.get("approved", False)
        
        if task_id and worker_id:
            # Update worker status
            if approved:
                self.worker_statuses[worker_id] = AgentStatus.COMPLETED
                # Remove completed task
                self.active_tasks.pop(task_id, None)
                self.task_assignments.pop(task_id, None)
            else:
                # Task needs revision - worker goes back to active
                self.worker_statuses[worker_id] = AgentStatus.ACTIVE
            
            # Broadcast review notification handling
            await self.agui_broadcaster.broadcast_dialogue_update(
                task_id=self.task_id,
                agent_id=self.agent_id,
                message_id=str(uuid.uuid4()),
                direction="input",
                content={
                    "type": "review_notification",
                    "data": review_result,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "team": self.team_name,
                        "action_taken": "task_completed" if approved else "task_revision_required"
                    }
                },
                sender="review_team"
            )
            
            logger.info(f"Supervisor {self.agent_id} handled review notification for task {task_id}: {'approved' if approved else 'needs revision'}")
    
    async def get_system_prompt(self) -> str:
        """Get supervisor-specific system prompt."""
        base_prompt = await super().get_system_prompt()
        
        supervisor_prompt = f"""{base_prompt}

SUPERVISOR RESPONSIBILITIES:
- Manage team '{self.team_name}' with {len(self.worker_agent_ids)} workers
- Delegate tasks to appropriate team members based on their capabilities
- Monitor worker progress and status
- Coordinate with other supervisors and the Global Supervisor
- Handle review notifications and task completion updates

TEAM WORKERS: {', '.join(self.worker_agent_ids)}

CURRENT TEAM STATUS:
- Active tasks: {len(self.active_tasks)}
- Worker statuses: {dict(self.worker_statuses)}

As a supervisor, focus on coordination, delegation, and ensuring your team delivers high-quality results."""
        
        return supervisor_prompt