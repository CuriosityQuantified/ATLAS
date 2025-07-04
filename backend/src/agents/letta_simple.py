"""
Module: letta_simple
Purpose: Simplified Letta integration that simulates memory without requiring server
Dependencies: BaseAgent
Used By: All supervisor and worker agents during MVP development
"""

from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleLettaAgentMixin:
    """
    Simplified Letta-style persistent memory for MVP.
    
    Key responsibilities:
    - Simulate Letta agent behavior
    - Store conversation history in memory
    - Extract tool calls from LLM responses
    
    Integrations:
    - BaseAgent: Inherits tracking/broadcasting
    - CallModel: Uses for actual LLM calls
    - Tool System: Parses tool calls from responses
    """
    
    def __init__(self, *args, **kwargs):
        # Initialize parent class first
        super().__init__(*args, **kwargs)
        
        # Then initialize Letta-style attributes
        self._init_simple_letta()
    
    def _init_simple_letta(self):
        """Initialize simplified Letta attributes"""
        self.letta_agent_id = f"simple_{self.agent_id}"
        self.conversation_history = []
        self.agent_memory = {
            "short_term": [],  # Recent messages
            "long_term": {},   # Key facts and knowledge
            "working_memory": {}  # Current task context
        }
        self.letta_initialized = False
        
    async def initialize_letta_agent(self, tools: List[Dict] = None):
        """Initialize agent with tools (simulated)"""
        self.agent_tools = tools or []
        self.letta_initialized = True
        logger.info(f"Initialized SimpleLetta agent: {self.letta_agent_id} with {len(self.agent_tools)} tools")
        
    async def send_to_letta(self, message: str, stream: bool = False) -> Dict[str, Any]:
        """
        Send message and get response with potential tool calls.
        Uses CallModel for actual LLM interaction.
        """
        
        if not self.letta_initialized:
            await self.initialize_letta_agent()
            
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update short-term memory (keep last 10 messages)
        self.agent_memory["short_term"] = self.conversation_history[-10:]
        
        # Build context with memory
        memory_context = self._build_memory_context()
        
        # Create enhanced prompt with memory and tools
        enhanced_prompt = f"""{memory_context}

User Message: {message}

{self._build_tool_context()}

Respond thoughtfully, considering your memory and available tools. If you need to use tools, format them as:
TOOL_CALL: tool_name
ARGUMENTS: {{"param1": "value1", "param2": "value2"}}

You can make multiple tool calls if needed."""

        # Use CallModel to get LLM response
        if hasattr(self, 'call_model') and self.call_model:
            response = await self.call_model.call_model(
                model_name="claude-3-5-haiku-20241022",
                system_prompt=await self.get_system_prompt() if hasattr(self, 'get_system_prompt') else "You are a helpful AI assistant.",
                most_recent_message=enhanced_prompt,
                max_tokens=1000,
                temperature=0.7
            )
            
            if response.success:
                # Parse response for tool calls
                content = response.content
                tool_calls = self._extract_tool_calls(content)
                
                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "tool_calls": tool_calls
                })
                
                return {
                    "content": content,
                    "tool_calls": tool_calls,
                    "raw_response": response,
                    "usage": {
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "total_tokens": response.total_tokens,
                        "cost_usd": response.cost_usd
                    }
                }
            else:
                return {
                    "content": f"Error: {response.error}",
                    "tool_calls": [],
                    "raw_response": response
                }
        else:
            # Fallback if CallModel not available
            return {
                "content": "I understand your request. However, I'm currently in simplified mode without full LLM capabilities.",
                "tool_calls": [],
                "raw_response": None
            }
    
    def _build_memory_context(self) -> str:
        """Build context string from agent memory"""
        context_parts = []
        
        # Add long-term memory facts
        if self.agent_memory["long_term"]:
            context_parts.append("Long-term Memory:")
            for key, value in self.agent_memory["long_term"].items():
                context_parts.append(f"- {key}: {value}")
        
        # Add working memory
        if self.agent_memory["working_memory"]:
            context_parts.append("\nCurrent Task Context:")
            for key, value in self.agent_memory["working_memory"].items():
                context_parts.append(f"- {key}: {value}")
        
        # Add recent conversation summary
        if self.agent_memory["short_term"]:
            context_parts.append("\nRecent Conversation:")
            for msg in self.agent_memory["short_term"][-3:]:  # Last 3 messages
                role = msg["role"].capitalize()
                content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                context_parts.append(f"- {role}: {content_preview}")
        
        return "\n".join(context_parts) if context_parts else "No previous context."
    
    def _build_tool_context(self) -> str:
        """Build tool context for the prompt"""
        if not self.agent_tools:
            return ""
            
        tool_desc = ["Available Tools:"]
        for tool in self.agent_tools:
            if "function" in tool:
                func = tool["function"]
                tool_desc.append(f"- {func['name']}: {func['description']}")
                
        return "\n".join(tool_desc)
    
    def _extract_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response"""
        tool_calls = []
        
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("TOOL_CALL:"):
                tool_name = line.replace("TOOL_CALL:", "").strip()
                
                # Look for arguments on next line
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("ARGUMENTS:"):
                    args_line = lines[i + 1].replace("ARGUMENTS:", "").strip()
                    try:
                        # Try to parse as JSON
                        arguments = json.loads(args_line)
                    except:
                        # Fallback to string
                        arguments = {"raw": args_line}
                else:
                    arguments = {}
                
                tool_calls.append({
                    "id": f"call_{len(tool_calls) + 1}",
                    "name": tool_name,
                    "arguments": arguments
                })
                
                i += 2  # Skip the arguments line
            else:
                i += 1
                
        return tool_calls
    
    async def load_conversation_context(self, chat_history: List[Dict[str, Any]]):
        """Load previous conversation history"""
        logger.info(f"Loading {len(chat_history)} messages into SimpleLetta context")
        
        # Convert chat history to our format
        for msg in chat_history:
            self.conversation_history.append({
                "role": "user" if msg.get("message_type") == "user" else "assistant",
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", "")
            })
        
        # Update short-term memory
        self.agent_memory["short_term"] = self.conversation_history[-10:]
    
    async def update_memory(self, key: str, value: Any):
        """Update specific memory in agent"""
        self.agent_memory["long_term"][key] = value
        logger.info(f"Updated SimpleLetta memory: {key}")
    
    async def update_working_memory(self, context: Dict[str, Any]):
        """Update working memory with current task context"""
        self.agent_memory["working_memory"].update(context)
        logger.info(f"Updated working memory with {len(context)} items")
    
    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent_id": self.letta_agent_id,
            "initialized": self.letta_initialized,
            "conversation_length": len(self.conversation_history),
            "short_term_memory_size": len(self.agent_memory["short_term"]),
            "long_term_facts": len(self.agent_memory["long_term"]),
            "working_memory_items": len(self.agent_memory["working_memory"]),
            "tools_available": len(self.agent_tools)
        }