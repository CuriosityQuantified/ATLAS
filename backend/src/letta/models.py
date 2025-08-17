"""Pydantic models for Letta integration."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"
    ERROR = "error"


class LettaAgentConfig(BaseModel):
    """Configuration for creating a Letta agent."""
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    model: str = Field("gpt-4", description="LLM model to use")
    persona: Optional[str] = Field(None, description="Agent persona/system prompt")
    human: Optional[str] = Field(None, description="Human description for the agent")
    preset: Optional[str] = Field(None, description="Preset configuration name")
    memory_human_str: Optional[str] = Field(None, description="Initial human memory")
    memory_persona_str: Optional[str] = Field(None, description="Initial persona memory")


class LettaAgent(BaseModel):
    """Letta agent model."""
    id: str = Field(..., description="Agent unique identifier")
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    status: AgentStatus = Field(AgentStatus.ACTIVE, description="Agent status")
    model: str = Field(..., description="LLM model")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    memory_stats: Dict[str, Any] = Field(default_factory=dict, description="Memory statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LettaMessage(BaseModel):
    """Message in a Letta conversation."""
    id: Optional[str] = Field(None, description="Message ID")
    agent_id: str = Field(..., description="Agent ID")
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LettaConversation(BaseModel):
    """Conversation with a Letta agent."""
    agent_id: str = Field(..., description="Agent ID")
    messages: List[LettaMessage] = Field(default_factory=list, description="Conversation messages")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation start time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")