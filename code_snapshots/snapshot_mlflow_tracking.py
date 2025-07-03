#!/usr/bin/env python3
"""
ATLAS MLflow Tracking System
Original architecture with dedicated tracking for multi-agent coordination
"""

import asyncio
import time
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging

try:
    import mlflow
    from mlflow.tracking import MlflowClient
except ImportError:
    mlflow = None
    MlflowClient = None

logger = logging.getLogger(__name__)


@dataclass
class AgentEvent:
    """Structure for tracking agent events."""
    event_id: str
    agent_id: str
    event_type: str  # "status_change", "task_start", "task_complete", "communication"
    timestamp: str
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


@dataclass
class TaskTracking:
    """Structure for tracking task progression."""
    task_id: str
    task_type: str
    status: str
    assigned_agent: str
    start_time: str
    end_time: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None


class ATLASMLflowTracker:
    """
    Original ATLAS MLflow Tracker for multi-agent system monitoring.
    Maintains separation of concerns between tracking and core agent logic.
    """
    
    def __init__(
        self, 
        tracking_uri: str = "http://localhost:5002",
        experiment_name: Optional[str] = None,
        auto_start_run: bool = False
    ):
        """Initialize ATLAS MLflow tracker."""
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name or f"ATLAS_Session_{int(time.time())}"
        self.current_run_id = None
        self.experiment_id = None
        
        if mlflow:
            mlflow.set_tracking_uri(tracking_uri)
            self.client = MlflowClient()
            
            # Create or get experiment
            try:
                self.experiment_id = mlflow.create_experiment(self.experiment_name)
                logger.info(f"Created MLflow experiment: {self.experiment_name} (ID: {self.experiment_id})")
            except Exception:
                # Experiment might already exist
                experiment = mlflow.get_experiment_by_name(self.experiment_name)
                self.experiment_id = experiment.experiment_id if experiment else "0"
                logger.info(f"Using existing MLflow experiment: {self.experiment_name} (ID: {self.experiment_id})")
            
            if auto_start_run:
                self.start_run()
        else:
            self.client = None
            logger.warning("MLflow not available - tracking disabled")
        
        # Session tracking data
        self.agent_events: List[AgentEvent] = []
        self.task_tracking: Dict[str, TaskTracking] = {}
        self.session_metrics: Dict[str, float] = {}
    
    def start_run(self, run_name: Optional[str] = None) -> Optional[str]:
        """Start a new MLflow run."""
        if not mlflow:
            return None
        
        try:
            run_name = run_name or f"ATLAS_Run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            run = mlflow.start_run(
                experiment_id=self.experiment_id,
                run_name=run_name
            )
            self.current_run_id = run.info.run_id
            
            # Log session metadata
            mlflow.log_params({
                "session_start": datetime.now().isoformat(),
                "tracking_uri": self.tracking_uri,
                "experiment_name": self.experiment_name
            })
            
            mlflow.set_tags({
                "atlas_component": "multi_agent_system",
                "tracking_version": "1.0",
                "session_type": "agent_coordination"
            })
            
            logger.info(f"Started MLflow run: {self.current_run_id}")
            return self.current_run_id
            
        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
            return None
    
    def end_run(self):
        """End the current MLflow run."""
        if mlflow and self.current_run_id:
            try:
                # Log session summary metrics
                self.log_session_summary()
                mlflow.end_run()
                logger.info(f"Ended MLflow run: {self.current_run_id}")
                self.current_run_id = None
            except Exception as e:
                logger.error(f"Failed to end MLflow run: {e}")
    
    def log_agent_status_change(
        self, 
        agent_id: str, 
        old_status: str, 
        new_status: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log agent status transitions."""
        if not mlflow or not self.current_run_id:
            return
        
        event = AgentEvent(
            event_id=f"status_{agent_id}_{int(time.time())}",
            agent_id=agent_id,
            event_type="status_change",
            timestamp=datetime.now().isoformat(),
            data={
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "transition": f"{old_status} -> {new_status}"
            },
            context=context
        )
        
        self.agent_events.append(event)
        
        try:
            # Log as metrics
            mlflow.log_metric(f"{agent_id}_status_changes", len([e for e in self.agent_events if e.agent_id == agent_id]))
            mlflow.log_metric("total_status_changes", len(self.agent_events))
            
            # Log as artifact
            self._log_json_artifact(
                asdict(event),
                f"agent_events/status_change_{agent_id}_{int(time.time())}.json"
            )
            
            # Update tags
            mlflow.set_tags({
                f"{agent_id}_current_status": new_status,
                f"{agent_id}_last_transition": f"{old_status}_to_{new_status}"
            })
            
        except Exception as e:
            logger.error(f"Failed to log agent status change: {e}")
    
    def log_task_assignment(
        self,
        task_id: str,
        task_type: str,
        assigned_agent: str,
        task_data: Optional[Dict[str, Any]] = None
    ):
        """Log task assignment to agents."""
        if not mlflow or not self.current_run_id:
            return
        
        task_tracking = TaskTracking(
            task_id=task_id,
            task_type=task_type,
            status="assigned",
            assigned_agent=assigned_agent,
            start_time=datetime.now().isoformat()
        )
        
        self.task_tracking[task_id] = task_tracking
        
        try:
            # Log task assignment
            mlflow.log_params({
                f"task_{task_id}_type": task_type,
                f"task_{task_id}_agent": assigned_agent
            })
            
            # Log as artifact
            self._log_json_artifact(
                {**asdict(task_tracking), "task_data": task_data or {}},
                f"tasks/assignment_{task_id}.json"
            )
            
            # Update metrics
            mlflow.log_metric("tasks_assigned", len(self.task_tracking))
            mlflow.log_metric(f"{assigned_agent}_tasks_assigned", 1.0)
            
        except Exception as e:
            logger.error(f"Failed to log task assignment: {e}")
    
    def log_task_completion(
        self,
        task_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        processing_time: Optional[float] = None
    ):
        """Log task completion with results."""
        if not mlflow or not self.current_run_id or task_id not in self.task_tracking:
            return
        
        task_tracking = self.task_tracking[task_id]
        task_tracking.end_time = datetime.now().isoformat()
        task_tracking.status = "completed" if success else "failed"
        task_tracking.result = result
        
        if processing_time:
            task_tracking.metrics = {"processing_time_seconds": processing_time}
        
        try:
            # Log completion metrics
            mlflow.log_metric("tasks_completed", len([t for t in self.task_tracking.values() if t.status == "completed"]))
            mlflow.log_metric("tasks_failed", len([t for t in self.task_tracking.values() if t.status == "failed"]))
            
            if processing_time:
                mlflow.log_metric(f"task_{task_id}_processing_time", processing_time)
                mlflow.log_metric("avg_task_processing_time", processing_time)
            
            # Log as artifact
            self._log_json_artifact(
                asdict(task_tracking),
                f"tasks/completion_{task_id}.json"
            )
            
            # Update tags
            mlflow.set_tags({
                f"task_{task_id}_status": task_tracking.status,
                "has_completed_tasks": "true"
            })
            
        except Exception as e:
            logger.error(f"Failed to log task completion: {e}")
    
    def log_agent_communication(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
        communication_id: Optional[str] = None
    ):
        """Log inter-agent communications."""
        if not mlflow or not self.current_run_id:
            return
        
        comm_id = communication_id or f"comm_{int(time.time())}"
        
        event = AgentEvent(
            event_id=comm_id,
            agent_id=from_agent,
            event_type="communication",
            timestamp=datetime.now().isoformat(),
            data={
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message_type": message_type,
                "content": content
            }
        )
        
        self.agent_events.append(event)
        
        try:
            # Log communication metrics
            mlflow.log_metric("total_communications", len([e for e in self.agent_events if e.event_type == "communication"]))
            mlflow.log_metric(f"{from_agent}_messages_sent", 1.0)
            mlflow.log_metric(f"{to_agent}_messages_received", 1.0)
            
            # Log as artifact
            self._log_json_artifact(
                asdict(event),
                f"communications/{message_type}_{from_agent}_to_{to_agent}_{int(time.time())}.json"
            )
            
            # Update tags
            mlflow.set_tags({
                f"agent_communication_{from_agent}_to_{to_agent}": "true",
                "has_agent_communication": "true"
            })
            
        except Exception as e:
            logger.error(f"Failed to log agent communication: {e}")
    
    def log_performance_metric(self, metric_name: str, value: float, step: Optional[int] = None):
        """Log custom performance metrics."""
        if not mlflow or not self.current_run_id:
            return
        
        try:
            if step is not None:
                mlflow.log_metric(metric_name, value, step=step)
            else:
                mlflow.log_metric(metric_name, value)
            
            # Update session metrics
            self.session_metrics[metric_name] = value
            
        except Exception as e:
            logger.error(f"Failed to log performance metric {metric_name}: {e}")
    
    def log_system_prompt(self, agent_id: str, system_prompt: str, prompt_source: str = "yaml"):
        """Log agent system prompts for tracking prompt engineering."""
        if not mlflow or not self.current_run_id:
            return
        
        try:
            # Log prompt as artifact
            prompt_data = {
                "agent_id": agent_id,
                "system_prompt": system_prompt,
                "prompt_source": prompt_source,
                "timestamp": datetime.now().isoformat(),
                "prompt_length": len(system_prompt),
                "word_count": len(system_prompt.split())
            }
            
            self._log_json_artifact(
                prompt_data,
                f"prompts/system_prompt_{agent_id}.json"
            )
            
            # Log prompt metrics
            mlflow.log_metric(f"{agent_id}_prompt_length", len(system_prompt))
            mlflow.log_metric(f"{agent_id}_prompt_words", len(system_prompt.split()))
            
            # Tag with prompt info
            mlflow.set_tags({
                f"{agent_id}_has_system_prompt": "true",
                f"{agent_id}_prompt_source": prompt_source
            })
            
        except Exception as e:
            logger.error(f"Failed to log system prompt for {agent_id}: {e}")
    
    def log_user_input(self, user_input: str, agent_id: str, context: Optional[Dict[str, Any]] = None):
        """Log user inputs for conversation tracking."""
        if not mlflow or not self.current_run_id:
            return
        
        try:
            input_data = {
                "user_input": user_input,
                "target_agent": agent_id,
                "timestamp": datetime.now().isoformat(),
                "input_length": len(user_input),
                "word_count": len(user_input.split()),
                "context": context or {}
            }
            
            self._log_json_artifact(
                input_data,
                f"user_inputs/input_{agent_id}_{int(time.time())}.json"
            )
            
            # Log input metrics
            mlflow.log_metric("total_user_inputs", 1.0)
            mlflow.log_metric(f"{agent_id}_user_inputs", 1.0)
            mlflow.log_metric("avg_input_length", len(user_input))
            
        except Exception as e:
            logger.error(f"Failed to log user input: {e}")
    
    def log_session_summary(self):
        """Log comprehensive session summary."""
        if not mlflow or not self.current_run_id:
            return
        
        try:
            summary = {
                "total_events": len(self.agent_events),
                "total_tasks": len(self.task_tracking),
                "completed_tasks": len([t for t in self.task_tracking.values() if t.status == "completed"]),
                "failed_tasks": len([t for t in self.task_tracking.values() if t.status == "failed"]),
                "session_duration": datetime.now().isoformat(),
                "session_metrics": self.session_metrics
            }
            
            # Calculate agent activity
            agent_activity = {}
            for event in self.agent_events:
                agent_id = event.agent_id
                if agent_id not in agent_activity:
                    agent_activity[agent_id] = {"events": 0, "status_changes": 0, "communications": 0}
                
                agent_activity[agent_id]["events"] += 1
                if event.event_type == "status_change":
                    agent_activity[agent_id]["status_changes"] += 1
                elif event.event_type == "communication":
                    agent_activity[agent_id]["communications"] += 1
            
            summary["agent_activity"] = agent_activity
            
            # Log summary as artifact
            self._log_json_artifact(summary, "session_summary.json")
            
            # Log summary metrics
            mlflow.log_metrics({
                "session_total_events": len(self.agent_events),
                "session_total_tasks": len(self.task_tracking),
                "session_success_rate": (summary["completed_tasks"] / max(1, summary["total_tasks"])) * 100
            })
            
        except Exception as e:
            logger.error(f"Failed to log session summary: {e}")
    
    def _log_json_artifact(self, data: Any, artifact_path: str):
        """Utility method to log JSON data as MLflow artifact."""
        if not mlflow:
            return
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(data, f, indent=2, default=str)
                temp_path = f.name
            
            mlflow.log_artifact(temp_path, artifact_path.rsplit('/', 1)[0] if '/' in artifact_path else "")
            os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"Failed to log JSON artifact {artifact_path}: {e}")
    
    def get_current_run_url(self) -> Optional[str]:
        """Get the MLflow UI URL for the current run."""
        if not self.current_run_id or not self.experiment_id:
            return None
        
        return f"{self.tracking_uri}/#/experiments/{self.experiment_id}/runs/{self.current_run_id}"
    
    def cleanup(self):
        """Cleanup tracker resources."""
        if self.current_run_id:
            self.end_run()
        logger.info("ATLASMLflowTracker cleaned up successfully")


# Global tracker instance for easy access
_global_tracker = None

def get_atlas_tracker() -> Optional[ATLASMLflowTracker]:
    """Get the global ATLAS tracker instance."""
    global _global_tracker
    return _global_tracker

def init_atlas_tracker(
    tracking_uri: str = "http://localhost:5002",
    experiment_name: Optional[str] = None,
    auto_start_run: bool = True
) -> ATLASMLflowTracker:
    """Initialize the global ATLAS tracker."""
    global _global_tracker
    _global_tracker = ATLASMLflowTracker(
        tracking_uri=tracking_uri,
        experiment_name=experiment_name,
        auto_start_run=auto_start_run
    )
    return _global_tracker