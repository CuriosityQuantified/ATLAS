# /Users/nicholaspate/Documents/ATLAS/backend/src/mlflow/tracking.py

import mlflow
from mlflow.tracking import MlflowClient
import json
import os
from typing import Dict, Any, List, Optional
import traceback

from backend.src.utils.cost_calculator import get_cost_and_pricing_details

# We will import the config class we already designed.
from .config.config import MLflowConfig

class ATLASMLflowTracker:
    """
    A centralized class to handle all interactions with the MLflow server for the ATLAS project.
    It provides a structured interface for tracking tasks, agents, performance, and artifacts.
    """

    def __init__(self, config: MLflowConfig):
        """
        Initializes the tracker and sets up the connection to the MLflow server.

        Args:
            config (MLflowConfig): A configuration object containing the tracking_uri.
        """
        mlflow.set_tracking_uri(config.tracking_uri)
        self.client = MlflowClient()

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

class ATLASMLflowTracker:
    # ... (__init__, start_task_run, start_agent_run methods are unchanged) ...

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
