#!/usr/bin/env python3
"""
Enhanced ATLAS MLflow Tracking System
Comprehensive tracking for LLM interactions, tool calls, and agent coordination
"""

import asyncio
import time
import json
import tempfile
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging

from .tracking import ATLASMLflowTracker

try:
    import mlflow
    from mlflow.tracking import MlflowClient
except ImportError:
    mlflow = None
    MlflowClient = None

logger = logging.getLogger(__name__)


@dataclass
class LLMInteraction:
    """Structure for tracking LLM model interactions."""
    interaction_id: str
    agent_id: str
    model_name: str
    provider: str
    system_prompt: str
    user_prompt: str
    response: str
    timestamp: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    success: bool
    error_message: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    request_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ToolCall:
    """Structure for tracking tool calls and external operations."""
    call_id: str
    agent_id: str
    tool_name: str
    tool_type: str  # "library", "api", "function", "agent_communication"
    input_parameters: Dict[str, Any]
    output_result: Any
    timestamp: str
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None
    tool_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConversationTurn:
    """Structure for tracking conversation turns with context."""
    turn_id: str
    agent_id: str
    turn_type: str  # "user_input", "agent_response", "system_message"
    content: str
    timestamp: str
    conversation_context: Dict[str, Any]
    parent_turn_id: Optional[str] = None
    token_count: Optional[int] = None


class EnhancedATLASTracker(ATLASMLflowTracker):
    """
    Enhanced MLflow tracker with comprehensive LLM and tool call monitoring.
    Extends the base ATLAS tracker with detailed interaction tracking.
    """
    
    def __init__(
        self, 
        tracking_uri: str = "http://localhost:5002",
        experiment_name: Optional[str] = None,
        auto_start_run: bool = False,
        enable_detailed_logging: bool = True
    ):
        """Initialize enhanced ATLAS MLflow tracker."""
        super().__init__(tracking_uri)
        
        self.enable_detailed_logging = enable_detailed_logging
        self.current_run_id = None
        
        # Enhanced tracking data
        self.llm_interactions: List[LLMInteraction] = []
        self.tool_calls: List[ToolCall] = []
        self.conversation_turns: List[ConversationTurn] = []
        
        # Auto-start run if requested
        if auto_start_run and experiment_name:
            try:
                mlflow.set_experiment(experiment_name)
                run = mlflow.start_run()
                self.current_run_id = run.info.run_id
                self.current_run = run
                logger.info(f"Auto-started MLflow run: {self.current_run_id}")
            except Exception as e:
                logger.error(f"Failed to auto-start MLflow run: {e}")
                self.current_run_id = None
        
        # Performance aggregations
        self.provider_stats: Dict[str, Dict[str, float]] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        self.session_metrics: Dict[str, float] = {}
        self.cost_tracking: Dict[str, float] = {
            "total_cost_usd": 0.0,
            "anthropic_cost": 0.0,
            "openai_cost": 0.0,
            "groq_cost": 0.0,
            "google_cost": 0.0
        }
        
        logger.info("Enhanced ATLAS tracker initialized with comprehensive monitoring")
    
    def log_task_assignment(self, task_id: str, task_type: str, assigned_agent: str, task_data: Dict[str, Any]):
        """Log task assignment information (compatibility method)."""
        if not self.current_run_id:
            logger.debug("No active run - skipping task assignment logging")
            return
            
        try:
            # Log task assignment as parameters and tags - the run is already active
            mlflow.log_params({
                "task_id": task_id,
                "task_type": task_type,
                "assigned_agent": assigned_agent
            })
            
            mlflow.set_tags({
                "task_type": task_type,
                "assigned_agent": assigned_agent,
                "has_task_assignment": "true"
            })
            
            # Log task data as artifact
            if self.enable_detailed_logging:
                assignment_data = {
                    "task_id": task_id,
                    "task_type": task_type,
                    "assigned_agent": assigned_agent,
                    "task_data": task_data,
                    "assigned_at": datetime.now().isoformat()
                }
                self._log_json_artifact(assignment_data, "task_assignment.json")
                    
            logger.info(f"Logged task assignment: {task_id} -> {assigned_agent}")
        except Exception as e:
            logger.error(f"Failed to log task assignment: {e}")
    
    def _log_json_artifact(self, data: Dict[str, Any], filename: str):
        """Helper method to log JSON data as MLflow artifact."""
        if not self.current_run_id:
            logger.debug(f"No active run - skipping artifact logging for {filename}")
            return
            
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(data, f, indent=2, default=str)
                temp_path = f.name
            
            # Log artifact directly - the run is already active
            mlflow.log_artifact(temp_path, filename)
            os.unlink(temp_path)  # Clean up temp file
            logger.debug(f"Successfully logged artifact: {filename}")
        except Exception as e:
            logger.error(f"Failed to log JSON artifact {filename}: {e}")
    
    def log_llm_interaction(
        self,
        interaction_id: str,
        agent_id: str,
        model_name: str,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        response: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
        success: bool = True,
        error_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        request_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log comprehensive LLM interaction data."""
        if not mlflow:
            return
        
        interaction = LLMInteraction(
            interaction_id=interaction_id,
            agent_id=agent_id,
            model_name=model_name,
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=response,
            timestamp=datetime.now().isoformat(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
            temperature=temperature,
            max_tokens=max_tokens,
            request_metadata=request_metadata or {}
        )
        
        self.llm_interactions.append(interaction)
        
        # Update cost tracking
        self.cost_tracking["total_cost_usd"] += cost_usd
        provider_key = f"{provider.lower()}_cost"
        if provider_key in self.cost_tracking:
            self.cost_tracking[provider_key] += cost_usd
        
        # Update provider stats
        if provider not in self.provider_stats:
            self.provider_stats[provider] = {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_latency": 0.0,
                "success_rate": 0.0
            }
        
        stats = self.provider_stats[provider]
        stats["total_calls"] += 1
        stats["total_tokens"] += interaction.total_tokens
        stats["total_cost"] += cost_usd
        stats["avg_latency"] = (stats["avg_latency"] * (stats["total_calls"] - 1) + latency_ms) / stats["total_calls"]
        
        # Calculate success rate
        successful_calls = len([i for i in self.llm_interactions if i.provider == provider and i.success])
        stats["success_rate"] = (successful_calls / stats["total_calls"]) * 100
        
        try:
            # Log detailed metrics only if we have an active run
            if not self.current_run_id:
                logger.debug("No active run - skipping metrics logging")
                return
                
            # Log detailed metrics directly - the run is already active
            mlflow.log_metrics({
                # Interaction-specific metrics
                f"{agent_id}_llm_calls": len([i for i in self.llm_interactions if i.agent_id == agent_id]),
                f"{agent_id}_total_tokens": sum(i.total_tokens for i in self.llm_interactions if i.agent_id == agent_id),
                f"{agent_id}_total_cost": sum(i.cost_usd for i in self.llm_interactions if i.agent_id == agent_id),
                f"{agent_id}_avg_latency": latency_ms,
                
                # Provider metrics
                f"{provider}_calls": stats["total_calls"],
                f"{provider}_avg_latency": stats["avg_latency"],
                f"{provider}_success_rate": stats["success_rate"],
                f"{provider}_total_cost": stats["total_cost"],
                
                # Global metrics
                "total_llm_interactions": len(self.llm_interactions),
                "total_tokens_used": sum(i.total_tokens for i in self.llm_interactions),
                "total_cost_usd": self.cost_tracking["total_cost_usd"]
            })
            
            # Update tags
            mlflow.set_tags({
                f"{agent_id}_uses_llm": "true",
                f"uses_{provider}": "true",
                f"uses_{model_name.replace('/', '_')}": "true",
                "has_llm_interactions": "true",
                f"{provider}_model_count": str(len(set(i.model_name for i in self.llm_interactions if i.provider == provider)))
            })
            
            # Log comprehensive interaction as artifact
            if self.enable_detailed_logging:
                interaction_data = asdict(interaction)
                
                # Add prompt analysis
                interaction_data["prompt_analysis"] = {
                    "system_prompt_length": len(system_prompt),
                    "system_prompt_words": len(system_prompt.split()),
                    "user_prompt_length": len(user_prompt),
                    "user_prompt_words": len(user_prompt.split()),
                    "response_length": len(response),
                    "response_words": len(response.split()),
                    "tokens_per_word_ratio": interaction.total_tokens / max(1, len(user_prompt.split()) + len(response.split()))
                }
                
                self._log_json_artifact(
                    interaction_data,
                    f"llm_interactions/{provider}/{model_name.replace('/', '_')}_{interaction_id}.json"
                )
            
            
        except Exception as e:
            logger.error(f"Failed to log LLM interaction: {e}")
    
    def log_tool_call(
        self,
        tool_call_id: str,
        agent_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        output_data: Any,
        execution_time_ms: float,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log detailed tool call information."""
        if not mlflow:
            return
        
        tool_call = ToolCall(
            call_id=tool_call_id,
            agent_id=agent_id,
            tool_name=tool_name,
            tool_type="library",  # Default tool type
            input_parameters=input_data,
            output_result=output_data,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=execution_time_ms,
            success=success,
            error_message=error_message,
            tool_metadata=metadata or {}
        )
        
        self.tool_calls.append(tool_call)
        
        try:
            # Log tool metrics
            agent_tool_calls = len([t for t in self.tool_calls if t.agent_id == agent_id])
            tool_type_calls = len([t for t in self.tool_calls if t.tool_type == "library"])
            successful_calls = len([t for t in self.tool_calls if t.tool_name == tool_name and t.success])
            total_tool_calls = len([t for t in self.tool_calls if t.tool_name == tool_name])
            
            mlflow.log_metrics({
                f"{agent_id}_tool_calls": agent_tool_calls,
                f"{agent_id}_{tool_name}_calls": len([t for t in self.tool_calls if t.agent_id == agent_id and t.tool_name == tool_name]),
                f"library_calls_total": tool_type_calls,
                f"{tool_name}_avg_latency": execution_time_ms,
                f"{tool_name}_success_rate": (successful_calls / max(1, total_tool_calls)) * 100,
                "total_tool_calls": len(self.tool_calls)
            })
            
            # Log tool call as artifact
            if self.enable_detailed_logging:
                tool_data = asdict(tool_call)
                
                # Add analysis
                tool_data["call_analysis"] = {
                    "input_size": len(str(input_data)),
                    "output_size": len(str(output_data)),
                    "processing_efficiency": len(str(output_data)) / max(1, execution_time_ms) * 1000,  # bytes per second
                    "parameter_count": len(input_data) if isinstance(input_data, dict) else 0
                }
                
                self._log_json_artifact(
                    tool_data,
                    f"tool_calls/library/{tool_name}_{tool_call_id}.json"
                )
            
            # Update tags
            mlflow.set_tags({
                f"{agent_id}_uses_library": "true",
                f"uses_tool_{tool_name}": "true",
                f"library_tools_count": str(len(set(t.tool_name for t in self.tool_calls if t.tool_type == "library"))),
                "has_tool_calls": "true"
            })
            
        except Exception as e:
            logger.error(f"Failed to log tool call: {e}")
    
    def log_conversation_turn(
        self,
        turn_id: str,
        agent_id: str,
        user_message: str,
        agent_response: str,
        turn_number: int,
        context: Dict[str, Any],
        response_time_ms: float,
        user_satisfaction: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log conversation turns for context tracking."""
        if not mlflow:
            return
        
        turn = ConversationTurn(
            turn_id=turn_id,
            agent_id=agent_id,
            turn_type="user_agent_interaction",
            content=f"User: {user_message}\nAgent: {agent_response}",
            timestamp=datetime.now().isoformat(),
            conversation_context=context,
            parent_turn_id=None,
            token_count=len(user_message.split()) + len(agent_response.split())
        )
        
        self.conversation_turns.append(turn)
        
        try:
            # Log conversation metrics
            agent_turns = len([t for t in self.conversation_turns if t.agent_id == agent_id])
            turn_type_count = len([t for t in self.conversation_turns if t.turn_type == "user_agent_interaction"])
            
            mlflow.log_metrics({
                f"{agent_id}_conversation_turns": agent_turns,
                f"user_agent_interaction_turns_total": turn_type_count,
                "total_conversation_turns": len(self.conversation_turns),
                "conversation_depth": len([t for t in self.conversation_turns if t.parent_turn_id is not None])
            })
            
            if turn.token_count:
                mlflow.log_metric(f"{agent_id}_conversation_tokens", turn.token_count)
            
            # Log as artifact
            if self.enable_detailed_logging:
                turn_data = asdict(turn)
                turn_data["turn_analysis"] = {
                    "content_length": len(turn.content),
                    "word_count": len(turn.content.split()),
                    "context_keys": list(context.keys()),
                    "has_parent": False,
                    "response_time_ms": response_time_ms,
                    "turn_number": turn_number,
                    "user_satisfaction": user_satisfaction
                }
                
                self._log_json_artifact(
                    turn_data,
                    f"conversations/{agent_id}/user_agent_interaction_{turn_id}.json"
                )
            
            # Update tags
            mlflow.set_tags({
                f"{agent_id}_has_conversations": "true",
                f"conversation_types": ",".join(set(t.turn_type for t in self.conversation_turns)),
                "has_conversation_history": "true"
            })
            
        except Exception as e:
            logger.error(f"Failed to log conversation turn: {e}")
    
    def log_agent_prompt_engineering(
        self,
        agent_id: str,
        prompt_version: str,
        system_prompt: str,
        persona_source: str,
        prompt_modifications: Optional[Dict[str, Any]] = None
    ):
        """Log agent prompt engineering and persona management."""
        if not mlflow:
            return
        
        try:
            prompt_data = {
                "agent_id": agent_id,
                "prompt_version": prompt_version,
                "persona_source": persona_source,
                "system_prompt": system_prompt,
                "timestamp": datetime.now().isoformat(),
                "prompt_modifications": prompt_modifications or {},
                "prompt_analysis": {
                    "character_count": len(system_prompt),
                    "word_count": len(system_prompt.split()),
                    "line_count": len(system_prompt.split('\n')),
                    "instruction_sections": system_prompt.count('INSTRUCTIONS:') + system_prompt.count('RESPONSIBILITIES:') + system_prompt.count('GUIDELINES:'),
                    "has_examples": 'example' in system_prompt.lower() or 'Example:' in system_prompt
                }
            }
            
            # Log prompt engineering artifact
            self._log_json_artifact(
                prompt_data,
                f"prompt_engineering/{agent_id}_prompt_v{prompt_version}.json"
            )
            
            # Log prompt metrics
            mlflow.log_metrics({
                f"{agent_id}_prompt_version": float(prompt_version.replace('.', '')),
                f"{agent_id}_prompt_length": len(system_prompt),
                f"{agent_id}_prompt_complexity": prompt_data["prompt_analysis"]["instruction_sections"]
            })
            
            # Tag prompt engineering
            mlflow.set_tags({
                f"{agent_id}_prompt_source": persona_source,
                f"{agent_id}_prompt_version": prompt_version,
                "has_prompt_engineering": "true"
            })
            
        except Exception as e:
            logger.error(f"Failed to log prompt engineering: {e}")
    
    def log_multi_agent_coordination(
        self,
        coordination_id: str,
        participating_agents: List[str],
        coordination_type: str,
        coordination_data: Dict[str, Any],
        success: bool = True,
        duration_ms: Optional[float] = None
    ):
        """Log multi-agent coordination patterns."""
        if not mlflow:
            return
        
        try:
            coordination_event = {
                "coordination_id": coordination_id,
                "participating_agents": participating_agents,
                "coordination_type": coordination_type,
                "coordination_data": coordination_data,
                "success": success,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "agent_count": len(participating_agents),
                    "coordination_complexity": len(coordination_data),
                    "efficiency_score": (len(participating_agents) / max(1, duration_ms or 1)) * 1000 if duration_ms else None
                }
            }
            
            # Log coordination artifact
            self._log_json_artifact(
                coordination_event,
                f"coordination/{coordination_type}_{coordination_id}.json"
            )
            
            # Log coordination metrics
            mlflow.log_metrics({
                f"coordination_{coordination_type}_count": len([c for c in self.agent_events if c.event_type == "coordination"]),
                "total_coordination_events": 1.0,
                "avg_coordination_agents": len(participating_agents)
            })
            
            if duration_ms:
                mlflow.log_metric(f"coordination_{coordination_type}_duration", duration_ms)
            
            # Tag coordination
            mlflow.set_tags({
                f"coordination_types": coordination_type,
                f"max_coordination_agents": str(len(participating_agents)),
                "has_multi_agent_coordination": "true"
            })
            
        except Exception as e:
            logger.error(f"Failed to log multi-agent coordination: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            "llm_interactions": {
                "total_interactions": len(self.llm_interactions),
                "successful_interactions": len([i for i in self.llm_interactions if i.success]),
                "total_tokens": sum(i.total_tokens for i in self.llm_interactions),
                "total_cost": self.cost_tracking["total_cost_usd"],
                "avg_latency": sum(i.latency_ms for i in self.llm_interactions) / max(1, len(self.llm_interactions)),
                "provider_breakdown": self.provider_stats
            },
            "tool_calls": {
                "total_calls": len(self.tool_calls),
                "successful_calls": len([t for t in self.tool_calls if t.success]),
                "avg_processing_time": sum(t.processing_time_ms for t in self.tool_calls) / max(1, len(self.tool_calls)),
                "tool_types": list(set(t.tool_type for t in self.tool_calls))
            },
            "conversations": {
                "total_turns": len(self.conversation_turns),
                "conversation_types": list(set(t.turn_type for t in self.conversation_turns)),
                "agents_in_conversation": list(set(t.agent_id for t in self.conversation_turns))
            },
            "cost_breakdown": self.cost_tracking,
            "session_metrics": self.session_metrics
        }
        
        return summary
    
    def get_current_run_url(self) -> Optional[str]:
        """Get the URL for the current MLflow run."""
        if self.current_run_id:
            # Get experiment ID from current run
            try:
                run = self.client.get_run(self.current_run_id)
                experiment_id = run.info.experiment_id
                return f"http://localhost:5002/#/experiments/{experiment_id}/runs/{self.current_run_id}"
            except Exception as e:
                logger.error(f"Failed to get run URL: {e}")
                return None
        return None
    
    def log_enhanced_session_summary(self):
        """Log enhanced session summary with all tracking data."""
        if not mlflow:
            return
        
        try:
            # Get comprehensive summary
            summary = self.get_performance_summary()
            
            # Add agent-specific summaries
            agent_summaries = {}
            for agent_id in set([i.agent_id for i in self.llm_interactions] + [t.agent_id for t in self.tool_calls]):
                agent_summaries[agent_id] = {
                    "llm_interactions": len([i for i in self.llm_interactions if i.agent_id == agent_id]),
                    "tool_calls": len([t for t in self.tool_calls if t.agent_id == agent_id]),
                    "conversation_turns": len([c for c in self.conversation_turns if c.agent_id == agent_id]),
                    "total_cost": sum(i.cost_usd for i in self.llm_interactions if i.agent_id == agent_id),
                    "total_tokens": sum(i.total_tokens for i in self.llm_interactions if i.agent_id == agent_id)
                }
            
            summary["agent_summaries"] = agent_summaries
            summary["enhanced_tracking_enabled"] = self.enable_detailed_logging
            
            # Log comprehensive summary
            self._log_json_artifact(summary, "enhanced_session_summary.json")
            
            # Log summary metrics
            mlflow.log_metrics({
                "enhanced_session_interactions": summary["llm_interactions"]["total_interactions"],
                "enhanced_session_tools": summary["tool_calls"]["total_calls"],
                "enhanced_session_conversations": summary["conversations"]["total_turns"],
                "enhanced_session_cost": summary["llm_interactions"]["total_cost"],
                "enhanced_session_agents": len(agent_summaries)
            })
            
            # Call parent session summary
            super().log_session_summary()
            
        except Exception as e:
            logger.error(f"Failed to log enhanced session summary: {e}")
    
    def cleanup(self):
        """Enhanced cleanup with performance summary."""
        try:
            if self.current_run_id:
                self.log_enhanced_session_summary()
                # End the current run
                mlflow.end_run()
                self.current_run_id = None
                self.current_run = None
            super().cleanup()
            logger.info("Enhanced ATLAS tracker cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during enhanced tracker cleanup: {e}")


# Enhanced global tracker
_enhanced_global_tracker = None

def get_enhanced_atlas_tracker() -> Optional[EnhancedATLASTracker]:
    """Get the global enhanced ATLAS tracker instance."""
    global _enhanced_global_tracker
    return _enhanced_global_tracker

def init_enhanced_atlas_tracker(
    tracking_uri: str = "http://localhost:5002",
    experiment_name: Optional[str] = None,
    auto_start_run: bool = True,
    enable_detailed_logging: bool = True
) -> EnhancedATLASTracker:
    """Initialize the global enhanced ATLAS tracker."""
    global _enhanced_global_tracker
    _enhanced_global_tracker = EnhancedATLASTracker(
        tracking_uri=tracking_uri,
        experiment_name=experiment_name,
        auto_start_run=auto_start_run,
        enable_detailed_logging=enable_detailed_logging
    )
    return _enhanced_global_tracker