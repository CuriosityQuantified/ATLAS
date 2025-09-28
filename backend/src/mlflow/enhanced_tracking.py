"""
Enhanced MLflow Tracking for ATLAS
Extends base tracking with comprehensive LLM and tool monitoring
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .tracking import ATLASMLflowTracker

logger = logging.getLogger(__name__)


@dataclass
class LLMInteraction:
    """Represents a single LLM interaction."""
    model: str
    provider: str
    messages: List[Dict[str, str]]
    response: str
    tokens_used: Dict[str, int]
    latency_ms: float
    timestamp: datetime


@dataclass
class ToolCall:
    """Represents a tool invocation."""
    tool_name: str
    agent_id: str
    parameters: Dict[str, Any]
    result: Any
    success: bool
    duration_ms: float
    timestamp: datetime


@dataclass
class ConversationTurn:
    """Represents a conversation turn between agents or with user."""
    sender: str
    receiver: str
    message: str
    context: Dict[str, Any]
    timestamp: datetime


class EnhancedATLASTracker(ATLASMLflowTracker):
    """
    Enhanced tracking with detailed LLM and tool call monitoring.
    """

    def __init__(self, experiment_name: str = "ATLAS_Enhanced"):
        """Initialize enhanced tracker."""
        super().__init__(experiment_name)
        self.llm_interactions: List[LLMInteraction] = []
        self.tool_calls: List[ToolCall] = []
        self.conversation_turns: List[ConversationTurn] = []

    def log_llm_interaction(self, interaction: LLMInteraction):
        """Log an LLM interaction."""
        self.llm_interactions.append(interaction)

        # Log metrics to MLflow
        self.log_metric(f"llm_{interaction.provider}_{interaction.model}_calls", 1)
        self.log_metric(f"llm_{interaction.provider}_tokens", interaction.tokens_used.get("total", 0))
        self.log_metric(f"llm_{interaction.provider}_latency_ms", interaction.latency_ms)

        logger.debug(f"Logged LLM interaction: {interaction.model} via {interaction.provider}")

    def log_tool_call(self, tool_call: ToolCall):
        """Log a tool invocation."""
        self.tool_calls.append(tool_call)

        # Log metrics
        self.log_metric(f"tool_{tool_call.tool_name}_calls", 1)
        self.log_metric(f"tool_{tool_call.tool_name}_duration_ms", tool_call.duration_ms)
        if tool_call.success:
            self.log_metric(f"tool_{tool_call.tool_name}_success", 1)
        else:
            self.log_metric(f"tool_{tool_call.tool_name}_failures", 1)

        logger.debug(f"Logged tool call: {tool_call.tool_name} by {tool_call.agent_id}")

    def log_conversation_turn(self, turn: ConversationTurn):
        """Log a conversation turn."""
        self.conversation_turns.append(turn)

        # Log conversation metrics
        self.log_metric("conversation_turns", 1)
        self.log_metric(f"messages_from_{turn.sender}", 1)

        logger.debug(f"Logged conversation: {turn.sender} -> {turn.receiver}")

    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        base_summary = super().get_session_summary()

        # Add enhanced tracking data
        base_summary.update({
            "llm_interactions": len(self.llm_interactions),
            "tool_calls": len(self.tool_calls),
            "conversation_turns": len(self.conversation_turns),
            "total_tokens": sum(i.tokens_used.get("total", 0) for i in self.llm_interactions),
            "avg_latency_ms": sum(i.latency_ms for i in self.llm_interactions) / len(self.llm_interactions) if self.llm_interactions else 0
        })

        return base_summary