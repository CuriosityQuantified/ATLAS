"""
Agent-specific MLflow Tracking for ATLAS
Tracks agent creation, tool invocations, planning outputs, and knowledge operations
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

import mlflow
from mlflow.tracking import MlflowClient

from .enhanced_tracking import EnhancedATLASTracker, ToolCall, ConversationTurn

logger = logging.getLogger(__name__)


@dataclass
class AgentCreation:
    """Represents agent creation with tools."""
    agent_id: str
    agent_type: str  # supervisor, research, analysis, writing
    tools_registered: List[str]
    model_config: Dict[str, Any]
    timestamp: datetime


@dataclass
class PlanOutput:
    """Represents a planning tool output."""
    plan_id: str
    agent_id: str
    task_description: str
    subtasks: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    estimated_duration_ms: float
    timestamp: datetime


@dataclass
class KnowledgeOperation:
    """Represents a knowledge storage/retrieval operation."""
    operation_type: str  # store, retrieve, update, delete
    agent_id: str
    knowledge_type: str  # research, analysis, writing
    content_size_bytes: int
    success: bool
    duration_ms: float
    timestamp: datetime


class AgentMLflowTracker(EnhancedATLASTracker):
    """
    Agent-specific MLflow tracking with tool-based architecture support.
    """

    def __init__(self, experiment_name: str = "ATLAS_Agents"):
        """Initialize agent tracker."""
        super().__init__(experiment_name)
        self.agent_creations: Dict[str, AgentCreation] = {}
        self.plan_outputs: List[PlanOutput] = []
        self.knowledge_operations: List[KnowledgeOperation] = []
        self.tool_metrics: Dict[str, Dict[str, Any]] = {}  # tool_name -> metrics

    def track_agent_creation(self,
                            agent_id: str,
                            agent_type: str,
                            tools: List[str],
                            model_config: Dict[str, Any]) -> None:
        """
        Track when an agent is created with its tools.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (supervisor, research, etc.)
            tools: List of tool names registered with the agent
            model_config: Model configuration (OpenAI model, temperature, etc.)
        """
        creation = AgentCreation(
            agent_id=agent_id,
            agent_type=agent_type,
            tools_registered=tools,
            model_config=model_config,
            timestamp=datetime.now()
        )

        self.agent_creations[agent_id] = creation

        # Log to MLflow
        self.log_metric(f"agents_{agent_type}_created", 1)
        self.log_metric(f"tools_per_agent_{agent_type}", len(tools))

        # Log agent configuration as artifact
        agent_config = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "tools": tools,
            "model_config": model_config,
            "created_at": creation.timestamp.isoformat()
        }

        self.log_artifact_json(agent_config, f"agents/{agent_id}_config.json")

        logger.info(f"Tracked agent creation: {agent_id} ({agent_type}) with {len(tools)} tools")

    def track_tool_invocation(self,
                             agent_id: str,
                             tool_name: str,
                             parameters: Dict[str, Any],
                             result: Any,
                             success: bool,
                             duration_ms: float) -> None:
        """
        Track a tool invocation by an agent.

        Args:
            agent_id: ID of the agent invoking the tool
            tool_name: Name of the tool being invoked
            parameters: Parameters passed to the tool
            result: Result returned by the tool
            success: Whether the invocation succeeded
            duration_ms: Time taken in milliseconds
        """
        # Use parent class method
        tool_call = ToolCall(
            tool_name=tool_name,
            agent_id=agent_id,
            parameters=parameters,
            result=result,
            success=success,
            duration_ms=duration_ms,
            timestamp=datetime.now()
        )

        self.log_tool_call(tool_call)

        # Update tool-specific metrics
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0
            }

        metrics = self.tool_metrics[tool_name]
        metrics["total_calls"] += 1
        if success:
            metrics["successful_calls"] += 1
        else:
            metrics["failed_calls"] += 1
        metrics["total_duration_ms"] += duration_ms
        metrics["avg_duration_ms"] = metrics["total_duration_ms"] / metrics["total_calls"]

        # Log aggregated metrics
        self.log_metric(f"tool_{tool_name}_avg_duration_ms", metrics["avg_duration_ms"])
        self.log_metric(f"tool_{tool_name}_success_rate",
                       metrics["successful_calls"] / metrics["total_calls"] if metrics["total_calls"] > 0 else 0)

    def track_planning_output(self,
                            plan_id: str,
                            agent_id: str,
                            task: str,
                            subtasks: List[Dict[str, Any]],
                            dependencies: Dict[str, List[str]],
                            duration_ms: float) -> None:
        """
        Track output from the planning tool.

        Args:
            plan_id: Unique identifier for the plan
            agent_id: ID of the agent that created the plan
            task: Main task description
            subtasks: List of subtask dictionaries
            dependencies: Task dependency mapping
            duration_ms: Time taken to generate plan
        """
        plan = PlanOutput(
            plan_id=plan_id,
            agent_id=agent_id,
            task_description=task,
            subtasks=subtasks,
            dependencies=dependencies,
            estimated_duration_ms=duration_ms,
            timestamp=datetime.now()
        )

        self.plan_outputs.append(plan)

        # Log metrics
        self.log_metric("plans_created", 1)
        self.log_metric("plan_subtasks_count", len(subtasks))
        self.log_metric("plan_generation_duration_ms", duration_ms)

        # Calculate plan complexity
        total_dependencies = sum(len(deps) for deps in dependencies.values())
        complexity_score = len(subtasks) + total_dependencies
        self.log_metric("plan_complexity_score", complexity_score)

        # Log plan as artifact
        plan_data = {
            "plan_id": plan_id,
            "agent_id": agent_id,
            "task": task,
            "subtasks": subtasks,
            "dependencies": dependencies,
            "duration_ms": duration_ms,
            "complexity_score": complexity_score,
            "created_at": plan.timestamp.isoformat()
        }

        self.log_artifact_json(plan_data, f"plans/{plan_id}.json")

        logger.info(f"Tracked plan: {plan_id} with {len(subtasks)} subtasks, complexity: {complexity_score}")

    def track_knowledge_operation(self,
                                 operation_type: str,
                                 agent_id: str,
                                 knowledge_type: str,
                                 content_size: int,
                                 success: bool,
                                 duration_ms: float) -> None:
        """
        Track knowledge storage/retrieval operations.

        Args:
            operation_type: Type of operation (store, retrieve, update, delete)
            agent_id: ID of the agent performing the operation
            knowledge_type: Type of knowledge (research, analysis, writing)
            content_size: Size of content in bytes
            success: Whether the operation succeeded
            duration_ms: Time taken in milliseconds
        """
        operation = KnowledgeOperation(
            operation_type=operation_type,
            agent_id=agent_id,
            knowledge_type=knowledge_type,
            content_size_bytes=content_size,
            success=success,
            duration_ms=duration_ms,
            timestamp=datetime.now()
        )

        self.knowledge_operations.append(operation)

        # Log metrics
        self.log_metric(f"knowledge_{operation_type}_operations", 1)
        self.log_metric(f"knowledge_{operation_type}_bytes", content_size)
        self.log_metric(f"knowledge_{operation_type}_duration_ms", duration_ms)

        if success:
            self.log_metric(f"knowledge_{operation_type}_success", 1)
        else:
            self.log_metric(f"knowledge_{operation_type}_failures", 1)

        # Calculate throughput
        throughput_mbps = (content_size / 1024 / 1024) / (duration_ms / 1000) if duration_ms > 0 else 0
        self.log_metric(f"knowledge_{operation_type}_throughput_mbps", throughput_mbps)

        logger.debug(f"Tracked knowledge {operation_type}: {knowledge_type} ({content_size} bytes) in {duration_ms}ms")

    def log_artifact_json(self, data: Dict[str, Any], artifact_path: str) -> None:
        """
        Helper method to log JSON data as an artifact.

        Args:
            data: Dictionary to save as JSON
            artifact_path: Path for the artifact
        """
        try:
            json_str = json.dumps(data, indent=2, default=str)
            mlflow.log_text(json_str, artifact_file=artifact_path)
        except Exception as e:
            logger.error(f"Failed to log artifact {artifact_path}: {e}")

    def get_tool_usage_summary(self) -> Dict[str, Any]:
        """
        Get summary of tool usage across all agents.

        Returns:
            Dictionary with tool usage statistics
        """
        summary = {
            "total_tool_calls": sum(m["total_calls"] for m in self.tool_metrics.values()),
            "unique_tools_used": len(self.tool_metrics),
            "tools": {}
        }

        for tool_name, metrics in self.tool_metrics.items():
            summary["tools"][tool_name] = {
                "calls": metrics["total_calls"],
                "success_rate": metrics["successful_calls"] / metrics["total_calls"] if metrics["total_calls"] > 0 else 0,
                "avg_duration_ms": metrics["avg_duration_ms"]
            }

        return summary

    def get_planning_effectiveness_metrics(self) -> Dict[str, Any]:
        """
        Calculate planning effectiveness metrics.

        Returns:
            Dictionary with planning metrics
        """
        if not self.plan_outputs:
            return {"plans_created": 0}

        total_subtasks = sum(len(p.subtasks) for p in self.plan_outputs)
        total_dependencies = sum(
            sum(len(deps) for deps in p.dependencies.values())
            for p in self.plan_outputs
        )

        return {
            "plans_created": len(self.plan_outputs),
            "total_subtasks": total_subtasks,
            "avg_subtasks_per_plan": total_subtasks / len(self.plan_outputs),
            "total_dependencies": total_dependencies,
            "avg_plan_generation_ms": sum(p.estimated_duration_ms for p in self.plan_outputs) / len(self.plan_outputs)
        }

    def get_knowledge_operations_summary(self) -> Dict[str, Any]:
        """
        Get summary of knowledge operations.

        Returns:
            Dictionary with knowledge operation statistics
        """
        summary = {
            "total_operations": len(self.knowledge_operations),
            "by_type": {},
            "total_bytes_processed": 0
        }

        for op in self.knowledge_operations:
            if op.operation_type not in summary["by_type"]:
                summary["by_type"][op.operation_type] = {
                    "count": 0,
                    "success_count": 0,
                    "total_bytes": 0,
                    "avg_duration_ms": 0
                }

            type_summary = summary["by_type"][op.operation_type]
            type_summary["count"] += 1
            if op.success:
                type_summary["success_count"] += 1
            type_summary["total_bytes"] += op.content_size_bytes

            # Update average duration
            prev_avg = type_summary["avg_duration_ms"]
            type_summary["avg_duration_ms"] = (
                (prev_avg * (type_summary["count"] - 1) + op.duration_ms) /
                type_summary["count"]
            )

            summary["total_bytes_processed"] += op.content_size_bytes

        return summary

    def get_comprehensive_session_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary including all agent-specific metrics.

        Returns:
            Dictionary with complete session summary
        """
        base_summary = self.get_session_summary()

        # Add agent-specific summaries
        base_summary.update({
            "agents_created": len(self.agent_creations),
            "agent_types": list(set(a.agent_type for a in self.agent_creations.values())),
            "tool_usage": self.get_tool_usage_summary(),
            "planning_metrics": self.get_planning_effectiveness_metrics(),
            "knowledge_operations": self.get_knowledge_operations_summary()
        })

        return base_summary

    def close(self) -> None:
        """
        Close the tracking session and log final summary.
        """
        try:
            # Log comprehensive summary as artifact
            summary = self.get_comprehensive_session_summary()
            self.log_artifact_json(summary, "session_summary.json")

            # Log final metrics
            self.log_metric("session_agents_created", len(self.agent_creations))
            self.log_metric("session_total_tool_calls",
                          sum(m["total_calls"] for m in self.tool_metrics.values()))
            self.log_metric("session_plans_created", len(self.plan_outputs))
            self.log_metric("session_knowledge_operations", len(self.knowledge_operations))

            logger.info("Agent MLflow tracking session closed successfully")

        except Exception as e:
            logger.error(f"Error closing tracking session: {e}")