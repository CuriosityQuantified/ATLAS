# /Users/nicholaspate/Documents/ATLAS/backend/src/mlflow/tracking.py

import mlflow
from mlflow.tracking import MlflowClient
import json
import os
from typing import Dict, Any, List, Optional
import traceback

from src.utils.cost_calculator import get_cost_and_pricing_details

# We will import the config class we already designed.
from .config.config import MLflowConfig

class ATLASMLflowTracker:
    """
    A centralized class to handle all interactions with the MLflow server for the ATLAS project.
    It provides a structured interface for tracking tasks, agents, performance, and artifacts.
    """

    def __init__(self, tracking_uri: str = "http://localhost:5002"):
        """
        Initializes the tracker and sets up the connection to the MLflow server.

        Args:
            tracking_uri (str): MLflow tracking server URI.
        """
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()
        # Cost calculation function available as get_cost_and_pricing_details
        self.current_run = None

    def start_task_run(self, task_id: str, task_metadata: Dict[str, Any]) -> str:
        """
        Starts a new parent run for a complete ATLAS task.

        Args:
            task_id (str): A unique identifier for the task.
            task_metadata (Dict[str, Any]): A dictionary with high-level task information.
                                           Required keys: 'user_id', 'initial_prompt'.
                                           Recommended keys for filtering: 'task_type', 'teams_involved'.

        Returns:
            str: The run_id of the newly created parent run.
        """
        mlflow.set_experiment(f"ATLAS_Task_{task_id}")
        
        with mlflow.start_run(run_name="Global_Supervisor_Run") as run:
            run_id = run.info.run_id
            
            # Log parameters that are present
            params_to_log = {}
            if "task_type" in task_metadata:
                params_to_log["task_type"] = task_metadata["task_type"]
            if "user_id" in task_metadata:
                params_to_log["user_id"] = task_metadata["user_id"]
            
            if params_to_log:
                mlflow.log_params(params_to_log)

            # Log complex data as artifacts
            if "initial_prompt" in task_metadata:
                mlflow.log_text(task_metadata["initial_prompt"], artifact_file="initial_prompt.txt")

            if "teams_involved" in task_metadata:
                teams_json = json.dumps(task_metadata["teams_involved"], indent=2)
                mlflow.log_text(teams_json, artifact_file="teams.json")

            return run_id

    def start_agent_run(self, parent_run_id: str, agent_id: str, agent_config: Dict[str, Any]) -> str:
        """
        Starts a nested run for a specific agent within a parent task run.

        Args:
            parent_run_id (str): The run_id of the parent task.
            agent_id (str): A unique identifier for the agent instance (e.g., "research_worker_1").
            agent_config (Dict[str, Any]): A dictionary with the agent's configuration.
                                          Required keys: 'agent_type', 'team', 'model_name', 'persona_prompt', 'tools_available'.

        Returns:
            str: The run_id of the new agent run.
        """
        with mlflow.start_run(run_name=agent_id, nested=True, run_id=parent_run_id) as run:
            run_id = run.info.run_id
            
            # Log simple parameters from config
            mlflow.log_params({
                "agent_type": agent_config.get("agent_type", "unknown"),
                "team": agent_config.get("team", "unknown"),
                "model_name": agent_config.get("model_name", "unknown"),
            })

            # Log complex data as artifacts
            if "persona_prompt" in agent_config:
                mlflow.log_text(agent_config["persona_prompt"], artifact_file="persona.txt")

            if "tools_available" in agent_config:
                tools_json = json.dumps(agent_config["tools_available"], indent=2)
                mlflow.log_text(tools_json, artifact_file="tools.json")

            # Set tags for easier filtering in the UI
            mlflow.set_tag("atlas.team", agent_config.get('team', 'unknown'))
            mlflow.set_tag("atlas.agent_type", agent_config.get('agent_type', 'unknown'))

            return run_id

    def log_agent_transaction(self, agent_run_id: str, model_name: str, input_tokens: int, output_tokens: int, artifacts: Optional[Dict[str, str]] = None, step: Optional[int] = None):
        """
        Logs a complete agent transaction, including performance, tokens, and calculated cost.

        Args:
            agent_run_id (str): The ID of the agent run to log against.
            model_name (str): The name of the model used for the transaction.
            input_tokens (int): The number of input tokens used.
            output_tokens (int): The number of output tokens generated.
            artifacts (Optional[Dict[str, str]]): Any text artifacts to log with this step.
            step (Optional[int]): The step for time-series metrics.
        """
        with mlflow.start_run(run_id=agent_run_id):
            
            # 1. Calculate cost and get pricing details
            final_cost, pricing_details = get_cost_and_pricing_details(
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # 2. Log parameters (data that doesn't change, like the provider)
            mlflow.log_param("model_provider", pricing_details["provider"])

            # 3. Log metrics (the data for this specific transaction)
            metrics_to_log = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_per_million_input_tokens": pricing_details["input_cost_per_million_tokens"],
                "cost_per_million_output_tokens": pricing_details["output_cost_per_million_tokens"],
                "final_cost_usd": final_cost
            }
            mlflow.log_metrics(metrics_to_log, step=step)

            # 4. Log any text artifacts
            if artifacts:
                for filename, content in artifacts.items():
                    mlflow.log_text(content, artifact_file=filename)

    def log_agent_error(self, agent_run_id: str, error: Exception):
        """
        Logs an error and marks the agent run as FAILED.

        Args:
            agent_run_id (str): The ID of the agent run.
            error (Exception): The exception that was raised during execution.
        """
        with mlflow.start_run(run_id=agent_run_id):
            mlflow.set_tag("status", "FAILED")
            mlflow.log_params({
                "error_type": type(error).__name__,
                "error_message": str(error)
            })
            
            # Log the full traceback as a text artifact for detailed debugging
            traceback_str = traceback.format_exc()
            mlflow.log_text(traceback_str, artifact_file="error_trace.log")

    def log_multi_modal_content(self, agent_run_id: str, content_type: str, content_size: int, 
                               processing_time: float, metadata: Optional[Dict[str, Any]] = None, 
                               step: Optional[int] = None):
        """
        Logs multi-modal content generation metrics for tracking content type distribution and performance.

        Args:
            agent_run_id (str): The ID of the agent run.
            content_type (str): Type of content ('text', 'image', 'file', 'audio', 'code', 'json', 'chart').
            content_size (int): Size of content in bytes.
            processing_time (float): Time taken to process/generate content in milliseconds.
            metadata (Optional[Dict[str, Any]]): Additional metadata about the content.
            step (Optional[int]): The step for time-series metrics.
        """
        with mlflow.start_run(run_id=agent_run_id):
            
            # Log content type distribution metrics
            content_metrics = {
                f"content_type_{content_type}_count": 1,
                f"content_type_{content_type}_size_bytes": content_size,
                f"content_type_{content_type}_processing_time_ms": processing_time,
                "total_content_items": 1,
                "total_content_size_bytes": content_size,
                "avg_processing_time_ms": processing_time
            }
            
            mlflow.log_metrics(content_metrics, step=step)
            
            # Log content type as parameter for filtering
            mlflow.log_param(f"content_types_generated", content_type)
            
            # Set tags for easier filtering
            mlflow.set_tag(f"atlas.content_type.{content_type}", "true")
            
            # Log metadata as artifacts if provided
            if metadata:
                metadata_json = json.dumps(metadata, indent=2)
                mlflow.log_text(metadata_json, artifact_file=f"content_metadata_{content_type}_{step or 'latest'}.json")

    def log_dialogue_message_stats(self, agent_run_id: str, message_direction: str, 
                                  content_type: str, token_count: Optional[int] = None,
                                  processing_time: Optional[float] = None, step: Optional[int] = None):
        """
        Logs statistics about agent dialogue messages for performance analysis.

        Args:
            agent_run_id (str): The ID of the agent run.
            message_direction (str): 'input' or 'output' direction of the message.
            content_type (str): Type of content in the message.
            token_count (Optional[int]): Number of tokens in text content.
            processing_time (Optional[float]): Time to process the message in milliseconds.
            step (Optional[int]): The step for time-series metrics.
        """
        with mlflow.start_run(run_id=agent_run_id):
            
            # Log dialogue flow metrics
            dialogue_metrics = {
                f"dialogue_{message_direction}_count": 1,
                f"dialogue_{message_direction}_{content_type}_count": 1,
            }
            
            if token_count is not None:
                dialogue_metrics[f"dialogue_{message_direction}_tokens"] = token_count
                dialogue_metrics[f"dialogue_{message_direction}_{content_type}_tokens"] = token_count
            
            if processing_time is not None:
                dialogue_metrics[f"dialogue_{message_direction}_processing_time_ms"] = processing_time
                
            mlflow.log_metrics(dialogue_metrics, step=step)
            
            # Set tags for dialogue analysis
            mlflow.set_tag(f"atlas.dialogue.{message_direction}", "true")
            mlflow.set_tag(f"atlas.dialogue.content_type.{content_type}", "true")

    def get_project_content_analytics(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieves analytics about content type distribution for a specific project/task.

        Args:
            task_id (str): The task ID to analyze.

        Returns:
            Dict[str, Any]: Analytics data including content type breakdown and performance metrics.
        """
        try:
            experiment_name = f"ATLAS_Task_{task_id}"
            experiment = self.client.get_experiment_by_name(experiment_name)
            
            if not experiment:
                return {"error": f"No experiment found for task {task_id}"}
            
            # Get all runs for this experiment
            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string="",
                order_by=["start_time DESC"]
            )
            
            analytics = {
                "task_id": task_id,
                "total_runs": len(runs),
                "content_type_distribution": {},
                "performance_metrics": {},
                "total_cost": 0.0,
                "total_tokens": 0,
                "avg_processing_time": 0.0
            }
            
            content_counts = {}
            total_processing_time = 0
            message_count = 0
            
            for run in runs:
                # Aggregate metrics
                for metric_key, metric_value in run.data.metrics.items():
                    if "content_type_" in metric_key and "_count" in metric_key:
                        content_type = metric_key.replace("content_type_", "").replace("_count", "")
                        content_counts[content_type] = content_counts.get(content_type, 0) + metric_value
                    
                    if "final_cost_usd" in metric_key:
                        analytics["total_cost"] += metric_value
                    
                    if "total_tokens" in metric_key:
                        analytics["total_tokens"] += metric_value
                    
                    if "processing_time_ms" in metric_key:
                        total_processing_time += metric_value
                        message_count += 1
            
            analytics["content_type_distribution"] = content_counts
            analytics["avg_processing_time"] = total_processing_time / message_count if message_count > 0 else 0
            
            return analytics
            
        except Exception as e:
            return {"error": f"Failed to retrieve analytics: {str(e)}"}

    def end_task_run(self, task_run_id: str, final_status: str = "FINISHED", 
                     summary: Optional[Dict[str, Any]] = None):
        """
        Marks a task run as complete and logs final summary metrics.

        Args:
            task_run_id (str): The ID of the task run to end.
            final_status (str): Final status of the task ('FINISHED', 'FAILED', 'CANCELLED').
            summary (Optional[Dict[str, Any]]): Final summary metrics and data.
        """
        with mlflow.start_run(run_id=task_run_id):
            mlflow.set_tag("status", final_status)
            
            if summary:
                # Log summary metrics
                summary_metrics = {}
                for key, value in summary.items():
                    if isinstance(value, (int, float)):
                        summary_metrics[f"final_{key}"] = value
                
                if summary_metrics:
                    mlflow.log_metrics(summary_metrics)
                
                # Log complex summary data as artifacts
                summary_json = json.dumps(summary, indent=2)
                mlflow.log_text(summary_json, artifact_file="task_summary.json")

    def start_agent_run(self, agent_id: str, agent_type: str, task_id: str, parent_run_id: Optional[str] = None):
        """Simple context manager for agent runs"""
        class AgentRunContext:
            def __init__(self, tracker, agent_id, agent_type, task_id):
                self.tracker = tracker
                self.agent_id = agent_id
                self.agent_type = agent_type
                self.task_id = task_id
                self.run_id = None
                
            def __enter__(self):
                mlflow.set_experiment(f"ATLAS_Agent_{self.agent_id}")
                self.run = mlflow.start_run(run_name=f"{self.agent_type}_{self.task_id}")
                self.run_id = self.run.info.run_id
                
                # Log basic parameters
                mlflow.log_params({
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type,
                    "task_id": self.task_id
                })
                
                return self.run_id
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    mlflow.set_tag("status", "FAILED")
                    mlflow.log_param("error_type", str(exc_type.__name__))
                    mlflow.log_param("error_message", str(exc_val))
                else:
                    mlflow.set_tag("status", "COMPLETED")
                mlflow.end_run()
        
        return AgentRunContext(self, agent_id, agent_type, task_id)
    
    def log_llm_call(self, run_id: str, model_provider: str, model_name: str, 
                     input_tokens: int, output_tokens: int, total_cost: float, 
                     latency: float, success: bool = True):
        """Log LLM call metrics"""
        # Log to active run if it matches, otherwise use nested run
        if mlflow.active_run() and mlflow.active_run().info.run_id == run_id:
            mlflow.log_metrics({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "total_cost": total_cost,
                "latency": latency
            })
            
            mlflow.log_params({
                "model_provider": model_provider,
                "model_name": model_name,
                "success": success
            })
        else:
            with mlflow.start_run(run_id=run_id, nested=True):
                mlflow.log_metrics({
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "total_cost": total_cost,
                    "latency": latency
                })
                
                mlflow.log_params({
                    "model_provider": model_provider,
                    "model_name": model_name,
                    "success": success
                })
    
    def log_dialogue_message_stats(self, run_id: str, direction: str, content_type: str, 
                                  token_count: int, processing_time: float):
        """Log dialogue message statistics"""
        # Log to active run if it matches, otherwise use nested run
        if mlflow.active_run() and mlflow.active_run().info.run_id == run_id:
            mlflow.log_metrics({
                f"{direction}_{content_type}_tokens": token_count,
                f"{direction}_processing_time": processing_time
            })
        else:
            with mlflow.start_run(run_id=run_id, nested=True):
                mlflow.log_metrics({
                    f"{direction}_{content_type}_tokens": token_count,
                    f"{direction}_processing_time": processing_time
                })
    
    def log_error(self, run_id: str, error_type: str, error_message: str, error_context: Dict):
        """Log error information"""
        # Check if we're already in the target run
        if mlflow.active_run() and mlflow.active_run().info.run_id == run_id:
            mlflow.set_tag("error_occurred", "true")
            mlflow.log_params({
                "error_type": error_type,
                "error_message": error_message[:100]  # Truncate long messages
            })
            
            # Log context as artifact
            context_json = json.dumps(error_context, indent=2)
            mlflow.log_text(context_json, artifact_file="error_context.json")
        else:
            with mlflow.start_run(run_id=run_id):
                mlflow.set_tag("error_occurred", "true")
                mlflow.log_params({
                    "error_type": error_type,
                    "error_message": error_message[:100]  # Truncate long messages
                })
                
                # Log context as artifact
                context_json = json.dumps(error_context, indent=2)
                mlflow.log_text(context_json, artifact_file="error_context.json")
