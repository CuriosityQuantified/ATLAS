"""
MLflow Dashboards for ATLAS Agent Monitoring

Provides visualization and analysis of agent metrics, tool usage, and performance
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType

logger = logging.getLogger(__name__)


class ATLASDashboards:
    """
    Dashboard generation and metrics analysis for ATLAS agents.
    """

    def __init__(self, tracking_uri: str = "http://localhost:5002"):
        """
        Initialize the dashboard manager.

        Args:
            tracking_uri: MLflow tracking server URI
        """
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()

    def get_tool_usage_frequency(self,
                                 experiment_name: str = "ATLAS_Agents",
                                 time_window_hours: int = 24) -> pd.DataFrame:
        """
        Get tool usage frequency across agents within a time window.

        Args:
            experiment_name: Name of the MLflow experiment
            time_window_hours: Number of hours to look back

        Returns:
            DataFrame with tool usage statistics
        """
        try:
            # Get experiment
            experiment = self.client.get_experiment_by_name(experiment_name)
            if not experiment:
                logger.warning(f"Experiment {experiment_name} not found")
                return pd.DataFrame()

            # Search for runs in time window
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            cutoff_timestamp = int(cutoff_time.timestamp() * 1000)

            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"attributes.start_time > {cutoff_timestamp}",
                view_type=ViewType.ACTIVE_ONLY
            )

            # Collect tool usage metrics
            tool_data = []
            for run in runs:
                metrics = run.data.metrics
                for metric_name, value in metrics.items():
                    if metric_name.startswith("tool_") and "_calls" in metric_name:
                        tool_name = metric_name.replace("tool_", "").replace("_calls", "")
                        tool_data.append({
                            "tool_name": tool_name,
                            "agent_id": run.info.run_name,
                            "calls": value,
                            "timestamp": run.info.start_time
                        })

            # Create DataFrame
            if tool_data:
                df = pd.DataFrame(tool_data)
                # Aggregate by tool
                summary = df.groupby("tool_name").agg({
                    "calls": "sum",
                    "agent_id": "nunique"
                }).rename(columns={"agent_id": "unique_agents"})
                summary["avg_calls_per_agent"] = summary["calls"] / summary["unique_agents"]
                return summary.sort_values("calls", ascending=False)

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to get tool usage frequency: {e}")
            return pd.DataFrame()

    def get_tool_execution_times(self,
                                 experiment_name: str = "ATLAS_Agents") -> pd.DataFrame:
        """
        Get average execution times for each tool.

        Args:
            experiment_name: Name of the MLflow experiment

        Returns:
            DataFrame with tool execution time statistics
        """
        try:
            experiment = self.client.get_experiment_by_name(experiment_name)
            if not experiment:
                return pd.DataFrame()

            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                view_type=ViewType.ACTIVE_ONLY
            )

            # Collect execution time metrics
            timing_data = []
            for run in runs:
                metrics = run.data.metrics
                for metric_name, value in metrics.items():
                    if metric_name.startswith("tool_") and "_duration_ms" in metric_name:
                        tool_name = metric_name.replace("tool_", "").replace("_duration_ms", "")
                        timing_data.append({
                            "tool_name": tool_name,
                            "duration_ms": value
                        })

            # Create DataFrame with statistics
            if timing_data:
                df = pd.DataFrame(timing_data)
                summary = df.groupby("tool_name")["duration_ms"].agg([
                    "mean", "median", "min", "max", "count"
                ]).round(2)
                summary.columns = ["avg_ms", "median_ms", "min_ms", "max_ms", "invocations"]
                return summary.sort_values("avg_ms", ascending=False)

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to get tool execution times: {e}")
            return pd.DataFrame()

    def get_planning_effectiveness_metrics(self,
                                          experiment_name: str = "ATLAS_Agents") -> Dict[str, Any]:
        """
        Analyze planning tool effectiveness across tasks.

        Args:
            experiment_name: Name of the MLflow experiment

        Returns:
            Dictionary with planning effectiveness metrics
        """
        try:
            experiment = self.client.get_experiment_by_name(experiment_name)
            if not experiment:
                return {}

            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                view_type=ViewType.ACTIVE_ONLY
            )

            # Collect planning metrics
            plan_metrics = {
                "total_plans": 0,
                "avg_subtasks": [],
                "avg_complexity": [],
                "generation_times": [],
                "success_rates": []
            }

            for run in runs:
                metrics = run.data.metrics
                if "plans_created" in metrics:
                    plan_metrics["total_plans"] += metrics["plans_created"]

                if "plan_subtasks_count" in metrics:
                    plan_metrics["avg_subtasks"].append(metrics["plan_subtasks_count"])

                if "plan_complexity_score" in metrics:
                    plan_metrics["avg_complexity"].append(metrics["plan_complexity_score"])

                if "plan_generation_duration_ms" in metrics:
                    plan_metrics["generation_times"].append(metrics["plan_generation_duration_ms"])

            # Calculate averages
            effectiveness = {
                "total_plans_created": plan_metrics["total_plans"],
                "avg_subtasks_per_plan": sum(plan_metrics["avg_subtasks"]) / len(plan_metrics["avg_subtasks"])
                                        if plan_metrics["avg_subtasks"] else 0,
                "avg_complexity_score": sum(plan_metrics["avg_complexity"]) / len(plan_metrics["avg_complexity"])
                                       if plan_metrics["avg_complexity"] else 0,
                "avg_generation_time_ms": sum(plan_metrics["generation_times"]) / len(plan_metrics["generation_times"])
                                         if plan_metrics["generation_times"] else 0
            }

            return effectiveness

        except Exception as e:
            logger.error(f"Failed to get planning effectiveness metrics: {e}")
            return {}

    def get_cost_tracking_summary(self,
                                 experiment_name: str = "ATLAS_Agents",
                                 time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Calculate costs per tool and agent.

        Args:
            experiment_name: Name of the MLflow experiment
            time_window_hours: Number of hours to look back

        Returns:
            Dictionary with cost breakdown
        """
        try:
            experiment = self.client.get_experiment_by_name(experiment_name)
            if not experiment:
                return {}

            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            cutoff_timestamp = int(cutoff_time.timestamp() * 1000)

            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"attributes.start_time > {cutoff_timestamp}",
                view_type=ViewType.ACTIVE_ONLY
            )

            # Cost calculations based on OpenAI pricing
            cost_per_tool = {}
            total_tokens = 0

            for run in runs:
                metrics = run.data.metrics

                # Track token usage
                if "llm_openai_tokens" in metrics:
                    total_tokens += metrics["llm_openai_tokens"]

                # Estimate costs per tool based on execution count and model
                for metric_name, value in metrics.items():
                    if metric_name.startswith("tool_") and "_calls" in metric_name:
                        tool_name = metric_name.replace("tool_", "").replace("_calls", "")

                        # Estimate tokens per tool call (rough estimates)
                        tokens_per_call = {
                            "plan_task": 1500,  # Planning is complex
                            "delegate_research": 800,
                            "delegate_analysis": 800,
                            "delegate_writing": 1000,
                            "save_output": 200,
                            "load_file": 150,
                            "create_todo": 100,
                            "update_todo_status": 50
                        }.get(tool_name, 300)  # Default estimate

                        if tool_name not in cost_per_tool:
                            cost_per_tool[tool_name] = {
                                "calls": 0,
                                "estimated_tokens": 0,
                                "estimated_cost": 0
                            }

                        cost_per_tool[tool_name]["calls"] += value
                        cost_per_tool[tool_name]["estimated_tokens"] += value * tokens_per_call

            # Calculate costs based on OpenAI pricing
            # GPT-4o: $2.50/1M input, $10.00/1M output (assuming 80/20 split)
            # GPT-4o-mini: $0.15/1M input, $0.60/1M output
            for tool_name, data in cost_per_tool.items():
                tokens = data["estimated_tokens"]
                # Rough cost calculation (80% input, 20% output)
                if tool_name == "plan_task" or "writing" in tool_name:
                    # Uses GPT-4o
                    data["estimated_cost"] = (tokens * 0.8 * 2.50 / 1_000_000) + (tokens * 0.2 * 10.00 / 1_000_000)
                else:
                    # Uses GPT-4o-mini
                    data["estimated_cost"] = (tokens * 0.8 * 0.15 / 1_000_000) + (tokens * 0.2 * 0.60 / 1_000_000)

            total_cost = sum(data["estimated_cost"] for data in cost_per_tool.values())

            return {
                "time_window_hours": time_window_hours,
                "total_estimated_tokens": total_tokens,
                "total_estimated_cost_usd": round(total_cost, 4),
                "cost_per_tool": {k: {**v, "estimated_cost": round(v["estimated_cost"], 4)}
                                 for k, v in cost_per_tool.items()},
                "cost_per_hour": round(total_cost / time_window_hours, 4) if time_window_hours > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to get cost tracking summary: {e}")
            return {}

    def get_agent_performance_comparison(self,
                                        experiment_name: str = "ATLAS_Agents") -> pd.DataFrame:
        """
        Compare performance metrics across different agent types.

        Args:
            experiment_name: Name of the MLflow experiment

        Returns:
            DataFrame comparing agent performance
        """
        try:
            experiment = self.client.get_experiment_by_name(experiment_name)
            if not experiment:
                return pd.DataFrame()

            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                view_type=ViewType.ACTIVE_ONLY
            )

            # Collect agent performance data
            agent_data = []
            for run in runs:
                params = run.data.params
                metrics = run.data.metrics

                if "agent_type" in params:
                    agent_data.append({
                        "agent_type": params["agent_type"],
                        "message_processing_ms": metrics.get("message_processing_ms", 0),
                        "tool_calls": sum(v for k, v in metrics.items()
                                        if k.endswith("_calls") and k.startswith("tool_")),
                        "success_rate": metrics.get("task_success_rate", 0),
                        "tokens_used": metrics.get("llm_openai_tokens", 0)
                    })

            # Create comparison DataFrame
            if agent_data:
                df = pd.DataFrame(agent_data)
                summary = df.groupby("agent_type").agg({
                    "message_processing_ms": "mean",
                    "tool_calls": "sum",
                    "success_rate": "mean",
                    "tokens_used": "sum"
                }).round(2)
                summary.columns = ["avg_response_ms", "total_tool_calls", "avg_success_rate", "total_tokens"]
                return summary

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to get agent performance comparison: {e}")
            return pd.DataFrame()

    def generate_dashboard_report(self,
                                 experiment_name: str = "ATLAS_Agents",
                                 time_window_hours: int = 24) -> str:
        """
        Generate a comprehensive text report of all dashboard metrics.

        Args:
            experiment_name: Name of the MLflow experiment
            time_window_hours: Number of hours to analyze

        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 60)
        report.append("ATLAS Agent Performance Dashboard Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Time Window: Last {time_window_hours} hours")
        report.append("=" * 60)
        report.append("")

        # Tool Usage Frequency
        report.append("## Tool Usage Frequency")
        report.append("-" * 40)
        tool_freq = self.get_tool_usage_frequency(experiment_name, time_window_hours)
        if not tool_freq.empty:
            report.append(tool_freq.to_string())
        else:
            report.append("No tool usage data available")
        report.append("")

        # Tool Execution Times
        report.append("## Tool Execution Times")
        report.append("-" * 40)
        exec_times = self.get_tool_execution_times(experiment_name)
        if not exec_times.empty:
            report.append(exec_times.to_string())
        else:
            report.append("No execution time data available")
        report.append("")

        # Planning Effectiveness
        report.append("## Planning Effectiveness")
        report.append("-" * 40)
        planning = self.get_planning_effectiveness_metrics(experiment_name)
        if planning:
            for key, value in planning.items():
                report.append(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        else:
            report.append("No planning data available")
        report.append("")

        # Cost Tracking
        report.append("## Cost Analysis")
        report.append("-" * 40)
        costs = self.get_cost_tracking_summary(experiment_name, time_window_hours)
        if costs:
            report.append(f"Total Estimated Cost: ${costs.get('total_estimated_cost_usd', 0):.4f}")
            report.append(f"Cost per Hour: ${costs.get('cost_per_hour', 0):.4f}")
            report.append("\nCost Breakdown by Tool:")
            for tool, data in costs.get("cost_per_tool", {}).items():
                report.append(f"  {tool}: ${data['estimated_cost']:.4f} ({data['calls']} calls)")
        else:
            report.append("No cost data available")
        report.append("")

        # Agent Performance Comparison
        report.append("## Agent Performance Comparison")
        report.append("-" * 40)
        agent_perf = self.get_agent_performance_comparison(experiment_name)
        if not agent_perf.empty:
            report.append(agent_perf.to_string())
        else:
            report.append("No agent performance data available")
        report.append("")

        report.append("=" * 60)
        report.append("End of Report")

        return "\n".join(report)

    def save_dashboard_artifacts(self,
                                run_id: str,
                                experiment_name: str = "ATLAS_Agents") -> None:
        """
        Save dashboard visualizations and reports as MLflow artifacts.

        Args:
            run_id: MLflow run ID to associate artifacts with
            experiment_name: Name of the MLflow experiment
        """
        try:
            # Generate report
            report = self.generate_dashboard_report(experiment_name)

            # Save as artifact
            with mlflow.start_run(run_id=run_id, nested=True):
                mlflow.log_text(report, "dashboards/performance_report.txt")

                # Save DataFrames as CSV artifacts
                tool_freq = self.get_tool_usage_frequency(experiment_name)
                if not tool_freq.empty:
                    mlflow.log_text(tool_freq.to_csv(), "dashboards/tool_frequency.csv")

                exec_times = self.get_tool_execution_times(experiment_name)
                if not exec_times.empty:
                    mlflow.log_text(exec_times.to_csv(), "dashboards/execution_times.csv")

                agent_perf = self.get_agent_performance_comparison(experiment_name)
                if not agent_perf.empty:
                    mlflow.log_text(agent_perf.to_csv(), "dashboards/agent_comparison.csv")

            logger.info(f"Dashboard artifacts saved for run {run_id}")

        except Exception as e:
            logger.error(f"Failed to save dashboard artifacts: {e}")