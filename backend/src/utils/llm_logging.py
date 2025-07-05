#!/usr/bin/env python3
"""
ATLAS LLM Call Logging Configuration

This module provides comprehensive logging for all LLM interactions in the ATLAS system.
It captures prompts, responses, token usage, costs, and timing information.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import os

# Create formatters
DETAILED_FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

PROMPT_RESPONSE_FORMATTER = logging.Formatter('%(message)s')

# Configure the main LLM logger
llm_logger = logging.getLogger('atlas.llm_calls')
llm_logger.setLevel(logging.INFO)

# Create file handler for all LLM calls
llm_log_dir = os.getenv('ATLAS_LOG_DIR', './logs')
os.makedirs(llm_log_dir, exist_ok=True)

llm_file_handler = logging.FileHandler(
    os.path.join(llm_log_dir, f'llm_calls_{datetime.now().strftime("%Y%m%d")}.log')
)
llm_file_handler.setFormatter(PROMPT_RESPONSE_FORMATTER)
llm_logger.addHandler(llm_file_handler)

# Create console handler for important LLM events
llm_console_handler = logging.StreamHandler()
llm_console_handler.setLevel(logging.WARNING)
llm_console_handler.setFormatter(DETAILED_FORMATTER)
llm_logger.addHandler(llm_console_handler)

# Letta-specific logger
letta_logger = logging.getLogger('atlas.letta_llm_calls')
letta_logger.setLevel(logging.INFO)

letta_file_handler = logging.FileHandler(
    os.path.join(llm_log_dir, f'letta_llm_calls_{datetime.now().strftime("%Y%m%d")}.log')
)
letta_file_handler.setFormatter(PROMPT_RESPONSE_FORMATTER)
letta_logger.addHandler(letta_file_handler)


class LLMCallLogger:
    """Comprehensive logger for LLM interactions"""
    
    @staticmethod
    def log_call_start(
        provider: str,
        model: str,
        method: str = "direct",
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None
    ):
        """Log the start of an LLM call"""
        llm_logger.info("="*80)
        llm_logger.info(f"[LLM CALL START] {datetime.now().isoformat()}")
        llm_logger.info(f"Provider: {provider.upper()} | Method: {method.upper()}")
        llm_logger.info(f"Model: {model}")
        if agent_id:
            llm_logger.info(f"Agent ID: {agent_id}")
        if task_id:
            llm_logger.info(f"Task ID: {task_id}")
    
    @staticmethod
    def log_prompt(
        system_prompt: Optional[str],
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ):
        """Log the prompt details"""
        if system_prompt:
            llm_logger.info(f"System Prompt: {system_prompt[:500]}..." if len(str(system_prompt)) > 500 else f"System Prompt: {system_prompt}")
        
        llm_logger.info("Messages:")
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            llm_logger.info(f"  [{i+1}] {role.upper()}: {content[:500]}..." if len(content) > 500 else f"  [{i+1}] {role.upper()}: {content}")
        
        llm_logger.info(f"Parameters: max_tokens={max_tokens}, temperature={temperature}")
        if kwargs:
            llm_logger.info(f"Additional params: {kwargs}")
    
    @staticmethod
    def log_response(
        content: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cost_usd: Optional[float] = None,
        response_time: Optional[float] = None,
        tool_calls: Optional[List[Dict]] = None
    ):
        """Log the response details"""
        llm_logger.info(f"Response: {content[:1000]}..." if len(content) > 1000 else f"Response: {content}")
        llm_logger.info(f"Tokens - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
        
        if cost_usd is not None:
            llm_logger.info(f"Cost: ${cost_usd:.4f}")
        
        if response_time is not None:
            llm_logger.info(f"Response Time: {response_time:.3f}s")
        
        if tool_calls:
            llm_logger.info(f"Tool Calls: {json.dumps(tool_calls, indent=2)}")
        
        llm_logger.info(f"[LLM CALL END] {datetime.now().isoformat()}")
        llm_logger.info("="*80)
    
    @staticmethod
    def log_error(
        provider: str,
        model: str,
        error_type: str,
        error_message: str,
        method: str = "direct"
    ):
        """Log LLM call errors"""
        llm_logger.error("="*80)
        llm_logger.error(f"[LLM CALL ERROR] {datetime.now().isoformat()}")
        llm_logger.error(f"Provider: {provider.upper()} | Method: {method.upper()} | Model: {model}")
        llm_logger.error(f"Error Type: {error_type}")
        llm_logger.error(f"Error Message: {error_message}")
        llm_logger.error("="*80)
    
    @staticmethod
    def log_letta_context(
        agent_id: str,
        memory_context: str,
        tool_context: str,
        user_message: str
    ):
        """Log Letta-specific context"""
        letta_logger.info("="*80)
        letta_logger.info(f"[LETTA AGENT CONTEXT] {datetime.now().isoformat()}")
        letta_logger.info(f"Agent ID: {agent_id}")
        letta_logger.info(f"Memory Context:\n{memory_context}")
        letta_logger.info(f"Available Tools:\n{tool_context}")
        letta_logger.info(f"User Message: {user_message}")
        letta_logger.info("="*80)
    
    @staticmethod
    def get_summary_stats() -> Dict[str, Any]:
        """Get summary statistics for the current session"""
        # This could be extended to read from logs and provide stats
        return {
            "total_calls": 0,  # Would need to track this
            "total_tokens": 0,
            "total_cost": 0.0,
            "providers_used": [],
            "models_used": []
        }


# Convenience function for quick logging
def log_llm_call(
    provider: str,
    model: str,
    prompt: str,
    response: str,
    tokens: Dict[str, int],
    cost: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Quick function to log a complete LLM call"""
    LLMCallLogger.log_call_start(provider, model)
    LLMCallLogger.log_prompt(None, [{"role": "user", "content": prompt}])
    LLMCallLogger.log_response(
        response,
        tokens.get('input', 0),
        tokens.get('output', 0),
        tokens.get('total', 0),
        cost
    )