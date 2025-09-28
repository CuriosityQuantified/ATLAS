"""
Cost Tracking for OpenAI API Usage in ATLAS

Tracks and monitors API costs for all OpenAI model invocations
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

import mlflow

logger = logging.getLogger(__name__)


@dataclass
class ModelPricing:
    """OpenAI model pricing information (prices per 1M tokens)."""
    input_price: float  # USD per 1M input tokens
    output_price: float  # USD per 1M output tokens
    model_name: str
    context_window: int


@dataclass
class APICall:
    """Represents a single API call with cost information."""
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: datetime
    agent_id: str
    task_id: str
    tool_name: Optional[str] = None


class OpenAICostTracker:
    """
    Tracks OpenAI API costs with MLflow integration.
    """

    # OpenAI pricing as of January 2025 (USD per 1M tokens)
    PRICING = {
        "gpt-4o": ModelPricing(
            input_price=2.50,
            output_price=10.00,
            model_name="gpt-4o",
            context_window=128000
        ),
        "gpt-4o-2024-11-20": ModelPricing(
            input_price=2.50,
            output_price=10.00,
            model_name="gpt-4o-2024-11-20",
            context_window=128000
        ),
        "gpt-4o-mini": ModelPricing(
            input_price=0.15,
            output_price=0.60,
            model_name="gpt-4o-mini",
            context_window=128000
        ),
        "gpt-4o-mini-2024-07-18": ModelPricing(
            input_price=0.15,
            output_price=0.60,
            model_name="gpt-4o-mini-2024-07-18",
            context_window=128000
        ),
        "text-embedding-3-small": ModelPricing(
            input_price=0.02,
            output_price=0.0,  # Embeddings don't have output tokens
            model_name="text-embedding-3-small",
            context_window=8191
        ),
        "text-embedding-3-large": ModelPricing(
            input_price=0.13,
            output_price=0.0,
            model_name="text-embedding-3-large",
            context_window=8191
        )
    }

    def __init__(self, mlflow_run_id: Optional[str] = None):
        """
        Initialize the cost tracker.

        Args:
            mlflow_run_id: Optional MLflow run ID for logging
        """
        self.mlflow_run_id = mlflow_run_id
        self.api_calls: List[APICall] = []
        self.cost_by_agent: Dict[str, float] = defaultdict(float)
        self.cost_by_model: Dict[str, float] = defaultdict(float)
        self.cost_by_task: Dict[str, float] = defaultdict(float)
        self.cost_by_tool: Dict[str, float] = defaultdict(float)
        self.total_cost = 0.0
        self.total_tokens = 0
        self.cost_alerts: List[Dict[str, Any]] = []

    def calculate_cost(self,
                      model: str,
                      input_tokens: int,
                      output_tokens: int) -> float:
        """
        Calculate cost for a specific API call.

        Args:
            model: Model name (e.g., "gpt-4o", "gpt-4o-mini")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Get pricing for model (handle model variants)
        base_model = model.split("-2024")[0] if "-2024" in model else model
        pricing = self.PRICING.get(base_model)

        if not pricing:
            logger.warning(f"Unknown model {model}, using GPT-4o-mini pricing as fallback")
            pricing = self.PRICING["gpt-4o-mini"]

        # Calculate costs (prices are per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * pricing.input_price
        output_cost = (output_tokens / 1_000_000) * pricing.output_price
        total_cost = input_cost + output_cost

        return total_cost

    def track_api_call(self,
                      model: str,
                      input_tokens: int,
                      output_tokens: int,
                      agent_id: str,
                      task_id: str,
                      tool_name: Optional[str] = None) -> float:
        """
        Track an OpenAI API call and calculate its cost.

        Args:
            model: Model used for the call
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            agent_id: ID of the agent making the call
            task_id: ID of the associated task
            tool_name: Optional name of tool that triggered the call

        Returns:
            Cost of the API call in USD
        """
        # Calculate cost
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        total_tokens = input_tokens + output_tokens

        # Create API call record
        api_call = APICall(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            timestamp=datetime.now(),
            agent_id=agent_id,
            task_id=task_id,
            tool_name=tool_name
        )

        # Store the call
        self.api_calls.append(api_call)

        # Update aggregates
        self.total_cost += cost
        self.total_tokens += total_tokens
        self.cost_by_agent[agent_id] += cost
        self.cost_by_model[model] += cost
        self.cost_by_task[task_id] += cost
        if tool_name:
            self.cost_by_tool[tool_name] += cost

        # Log to MLflow if available
        if self.mlflow_run_id:
            try:
                with mlflow.start_run(run_id=self.mlflow_run_id, nested=True):
                    mlflow.log_metric(f"cost_usd_{model.replace('-', '_')}", cost)
                    mlflow.log_metric("total_cost_usd", self.total_cost)
                    mlflow.log_metric("total_tokens", self.total_tokens)
                    mlflow.log_metric(f"tokens_{model.replace('-', '_')}", total_tokens)
            except Exception as e:
                logger.warning(f"Failed to log cost metrics to MLflow: {e}")

        # Check for cost alerts
        self._check_cost_thresholds(cost, model, agent_id)

        logger.debug(f"Tracked API call: {model} - ${cost:.4f} ({total_tokens} tokens)")

        return cost

    def _check_cost_thresholds(self, cost: float, model: str, agent_id: str) -> None:
        """
        Check if cost exceeds alert thresholds.

        Args:
            cost: Cost of the current API call
            model: Model used
            agent_id: Agent that made the call
        """
        # Alert thresholds
        SINGLE_CALL_THRESHOLD = 0.10  # Alert if single call exceeds $0.10
        HOURLY_THRESHOLD = 1.00  # Alert if hourly rate exceeds $1.00
        DAILY_THRESHOLD = 10.00  # Alert if daily total exceeds $10.00

        # Check single call threshold
        if cost > SINGLE_CALL_THRESHOLD:
            alert = {
                "type": "single_call_exceeded",
                "threshold": SINGLE_CALL_THRESHOLD,
                "actual": cost,
                "model": model,
                "agent_id": agent_id,
                "timestamp": datetime.now()
            }
            self.cost_alerts.append(alert)
            logger.warning(f"Cost alert: Single call exceeded ${SINGLE_CALL_THRESHOLD:.2f} - "
                         f"{model} cost ${cost:.4f}")

        # Check daily threshold
        if self.total_cost > DAILY_THRESHOLD:
            alert = {
                "type": "daily_total_exceeded",
                "threshold": DAILY_THRESHOLD,
                "actual": self.total_cost,
                "timestamp": datetime.now()
            }
            self.cost_alerts.append(alert)
            logger.warning(f"Cost alert: Daily total exceeded ${DAILY_THRESHOLD:.2f} - "
                         f"Current total ${self.total_cost:.4f}")

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive cost summary.

        Returns:
            Dictionary with cost breakdown and statistics
        """
        if not self.api_calls:
            return {
                "total_cost_usd": 0,
                "total_tokens": 0,
                "call_count": 0
            }

        # Calculate time-based metrics
        time_span = (self.api_calls[-1].timestamp - self.api_calls[0].timestamp).total_seconds() / 3600
        hourly_rate = self.total_cost / time_span if time_span > 0 else 0

        # Find most expensive calls
        expensive_calls = sorted(self.api_calls, key=lambda x: x.cost_usd, reverse=True)[:5]

        return {
            "total_cost_usd": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
            "call_count": len(self.api_calls),
            "hourly_rate_usd": round(hourly_rate, 4),
            "avg_cost_per_call": round(self.total_cost / len(self.api_calls), 4),
            "avg_tokens_per_call": self.total_tokens // len(self.api_calls),
            "cost_by_model": {k: round(v, 4) for k, v in self.cost_by_model.items()},
            "cost_by_agent": {k: round(v, 4) for k, v in self.cost_by_agent.items()},
            "cost_by_task": {k: round(v, 4) for k, v in self.cost_by_task.items()},
            "cost_by_tool": {k: round(v, 4) for k, v in self.cost_by_tool.items()},
            "most_expensive_calls": [
                {
                    "model": call.model,
                    "cost": round(call.cost_usd, 4),
                    "tokens": call.total_tokens,
                    "agent": call.agent_id,
                    "tool": call.tool_name
                }
                for call in expensive_calls
            ],
            "alerts": self.cost_alerts
        }

    def get_cost_by_time_window(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get costs for a specific time window.

        Args:
            hours: Number of hours to look back

        Returns:
            Cost data for the time window
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        window_calls = [call for call in self.api_calls if call.timestamp >= cutoff_time]

        if not window_calls:
            return {"window_hours": hours, "cost_usd": 0, "calls": 0}

        window_cost = sum(call.cost_usd for call in window_calls)
        window_tokens = sum(call.total_tokens for call in window_calls)

        return {
            "window_hours": hours,
            "cost_usd": round(window_cost, 4),
            "tokens": window_tokens,
            "calls": len(window_calls),
            "hourly_rate": round(window_cost / hours, 4) if hours > 0 else 0
        }

    def project_daily_cost(self) -> float:
        """
        Project daily cost based on current usage patterns.

        Returns:
            Projected daily cost in USD
        """
        if not self.api_calls:
            return 0.0

        # Calculate time span of usage
        time_span = (self.api_calls[-1].timestamp - self.api_calls[0].timestamp).total_seconds() / 3600

        if time_span == 0:
            return 0.0

        # Project to 24 hours
        hourly_rate = self.total_cost / time_span
        daily_projection = hourly_rate * 24

        return round(daily_projection, 2)

    def get_token_efficiency_metrics(self) -> Dict[str, Any]:
        """
        Calculate token efficiency metrics.

        Returns:
            Dictionary with efficiency metrics
        """
        if not self.api_calls:
            return {}

        total_input = sum(call.input_tokens for call in self.api_calls)
        total_output = sum(call.output_tokens for call in self.api_calls)

        # Calculate efficiency by model
        model_efficiency = {}
        for model in self.cost_by_model.keys():
            model_calls = [c for c in self.api_calls if c.model == model]
            if model_calls:
                model_tokens = sum(c.total_tokens for c in model_calls)
                model_cost = self.cost_by_model[model]
                model_efficiency[model] = {
                    "tokens_per_dollar": int(model_tokens / model_cost) if model_cost > 0 else 0,
                    "avg_tokens_per_call": model_tokens // len(model_calls),
                    "input_output_ratio": sum(c.input_tokens for c in model_calls) /
                                         max(sum(c.output_tokens for c in model_calls), 1)
                }

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "input_output_ratio": total_input / max(total_output, 1),
            "tokens_per_dollar": int(self.total_tokens / self.total_cost) if self.total_cost > 0 else 0,
            "model_efficiency": model_efficiency
        }

    def export_cost_report(self) -> str:
        """
        Generate a detailed cost report.

        Returns:
            Formatted cost report string
        """
        summary = self.get_cost_summary()
        efficiency = self.get_token_efficiency_metrics()
        daily_projection = self.project_daily_cost()

        report = []
        report.append("=" * 60)
        report.append("OpenAI API Cost Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")

        # Overall Summary
        report.append(f"Total Cost: ${summary['total_cost_usd']:.4f}")
        report.append(f"Total Tokens: {summary['total_tokens']:,}")
        report.append(f"Total API Calls: {summary['call_count']}")
        report.append(f"Average Cost per Call: ${summary['avg_cost_per_call']:.4f}")
        report.append(f"Hourly Rate: ${summary['hourly_rate_usd']:.4f}")
        report.append(f"Projected Daily Cost: ${daily_projection:.2f}")
        report.append("")

        # Cost by Model
        report.append("Cost by Model:")
        for model, cost in summary['cost_by_model'].items():
            report.append(f"  {model}: ${cost:.4f}")
        report.append("")

        # Token Efficiency
        if efficiency:
            report.append("Token Efficiency:")
            report.append(f"  Total Input Tokens: {efficiency['total_input_tokens']:,}")
            report.append(f"  Total Output Tokens: {efficiency['total_output_tokens']:,}")
            report.append(f"  Input/Output Ratio: {efficiency['input_output_ratio']:.2f}")
            report.append(f"  Tokens per Dollar: {efficiency['tokens_per_dollar']:,}")
        report.append("")

        # Most Expensive Calls
        if summary['most_expensive_calls']:
            report.append("Top 5 Most Expensive Calls:")
            for i, call in enumerate(summary['most_expensive_calls'], 1):
                report.append(f"  {i}. {call['model']}: ${call['cost']:.4f} "
                            f"({call['tokens']} tokens, Agent: {call['agent']})")
        report.append("")

        # Alerts
        if summary['alerts']:
            report.append(f"⚠️  Cost Alerts ({len(summary['alerts'])} total):")
            for alert in summary['alerts'][-5:]:  # Show last 5 alerts
                report.append(f"  - {alert['type']}: ${alert['actual']:.4f} > ${alert['threshold']:.2f}")

        return "\n".join(report)

    def reset(self) -> None:
        """Reset all tracking data."""
        self.api_calls.clear()
        self.cost_by_agent.clear()
        self.cost_by_model.clear()
        self.cost_by_task.clear()
        self.cost_by_tool.clear()
        self.cost_alerts.clear()
        self.total_cost = 0.0
        self.total_tokens = 0


# Import timedelta for the time window function
from datetime import timedelta