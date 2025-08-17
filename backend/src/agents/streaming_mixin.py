"""
Module: streaming_mixin
Purpose: Add streaming capabilities to agents for real-time updates
Dependencies: AG-UI broadcaster, CallModel
Used By: Supervisor agents for live updates
"""

import asyncio
import json
import re
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StreamingAgentMixin:
    """
    Adds streaming capabilities to agents for real-time user experience.
    
    Features:
    - Stream LLM tokens as they're generated
    - Show thinking process (if model supports it)
    - Display tool call construction in real-time
    - Animate typing indicators
    """
    
    async def send_typing_indicator(self, is_typing: bool = True):
        """Send typing indicator to frontend"""
        if hasattr(self, 'agui_broadcaster') and self.agui_broadcaster:
            try:
                await self.agui_broadcaster.broadcast_agent_status_changed(
                    task_id=self.task_id,
                    agent_id=self.agent_id,
                    old_status="idle" if not is_typing else "typing",
                    new_status="typing" if is_typing else "idle"
                )
            except AttributeError:
                # Fallback to broadcast_agent_status if the _changed version doesn't exist
                if hasattr(self.agui_broadcaster, 'broadcast_agent_status'):
                    await self.agui_broadcaster.broadcast_agent_status(
                        task_id=self.task_id,
                        agent_id=self.agent_id,
                        old_status="idle" if not is_typing else "typing",
                        new_status="typing" if is_typing else "idle"
                    )
                else:
                    logger.warning("AG-UI broadcaster missing status change methods")
    
    async def stream_to_letta(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response from LLM with real-time updates.
        Yields chunks as they arrive.
        """
        
        if not self.letta_initialized:
            await self.initialize_letta_agent()
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send typing indicator
        await self.send_typing_indicator(True)
        
        # Build context
        memory_context = self._build_memory_context()
        enhanced_prompt = f"""{memory_context}

User Message: {message}

{self._build_tool_context()}

Think step by step about what the user is asking. Show your reasoning process.
If you need to use tools, format them as:
TOOL_CALL: tool_name
ARGUMENTS: {{"param1": "value1", "param2": "value2"}}"""
        
        # Stream from model
        accumulated_content = ""
        current_tool_call = None
        tool_calls = []
        is_in_thinking = False
        thinking_content = ""
        
        try:
            # Use streaming API if available
            if hasattr(self, 'call_model') and self.call_model:
                # For Claude 3.5, we can request thinking tokens
                stream = await self._create_llm_stream(enhanced_prompt)
                
                async for chunk in stream:
                    # Parse chunk based on provider
                    chunk_content = self._extract_chunk_content(chunk)
                    
                    if chunk_content:
                        accumulated_content += chunk_content
                        
                        # Check for thinking markers (Claude 3.5 Sonnet supports <thinking> tags)
                        if "<thinking>" in chunk_content and not is_in_thinking:
                            is_in_thinking = True
                            # Broadcast thinking started
                            await self._broadcast_thinking_update("started", "")
                            continue
                        
                        if "</thinking>" in chunk_content and is_in_thinking:
                            is_in_thinking = False
                            # Broadcast complete thinking
                            await self._broadcast_thinking_update("complete", thinking_content)
                            thinking_content = ""
                            continue
                        
                        if is_in_thinking:
                            thinking_content += chunk_content
                            # Broadcast thinking chunk
                            await self._broadcast_thinking_update("chunk", chunk_content)
                            continue
                        
                        # Check for tool call patterns
                        tool_match = re.search(r'TOOL_CALL:\s*(\w+)', chunk_content)
                        if tool_match and not current_tool_call:
                            current_tool_call = {
                                "name": tool_match.group(1),
                                "arguments": {},
                                "id": f"stream_{self.agent_id}_{int(datetime.now().timestamp())}"
                            }
                            # Broadcast tool call started
                            await self._broadcast_tool_stream_update(
                                current_tool_call["id"],
                                "started",
                                current_tool_call["name"]
                            )
                        
                        # Check for arguments
                        if current_tool_call:
                            args_match = re.search(r'ARGUMENTS:\s*(\{[^}]+\})', accumulated_content)
                            if args_match:
                                try:
                                    current_tool_call["arguments"] = json.loads(args_match.group(1))
                                    tool_calls.append(current_tool_call)
                                    
                                    # Broadcast tool call ready
                                    await self._broadcast_tool_stream_update(
                                        current_tool_call["id"],
                                        "ready",
                                        current_tool_call["name"],
                                        current_tool_call["arguments"]
                                    )
                                    
                                    current_tool_call = None
                                except json.JSONDecodeError:
                                    pass
                        
                        # Yield content chunk for display
                        yield {
                            "type": "content",
                            "content": chunk_content,
                            "timestamp": datetime.now().isoformat()
                        }
                
                # Stop typing indicator
                await self.send_typing_indicator(False)
                
                # Add complete response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": accumulated_content,
                    "timestamp": datetime.now().isoformat(),
                    "tool_calls": tool_calls
                })
                
                # Yield final response
                yield {
                    "type": "complete",
                    "content": accumulated_content,
                    "tool_calls": tool_calls,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            await self.send_typing_indicator(False)
            
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _create_llm_stream(self, prompt: str) -> AsyncGenerator:
        """Create streaming response from LLM provider"""
        # This would use the appropriate streaming API based on provider
        # For now, simulate streaming by yielding words
        
        # Example for Claude streaming (would use actual API)
        if "claude" in getattr(self, 'model_name', 'claude-3-5-haiku-20241022'):
            # Simulate streaming response
            response = """<thinking>
The user sent a greeting "hi". This is a simple social interaction. I should:
1. Acknowledge the greeting
2. Analyze what they might need
3. Offer assistance
</thinking>

I'll analyze your request and see how I can help.

TOOL_CALL: analyze_request
ARGUMENTS: {"query": "Analyzing your request..."}"""
            
            # Simulate streaming by yielding words
            words = response.split(' ')
            for i, word in enumerate(words):
                await asyncio.sleep(0.05)  # Simulate network delay
                yield {"content": word + (' ' if i < len(words) - 1 else '')}
    
    def _extract_chunk_content(self, chunk: Any) -> str:
        """Extract content from streaming chunk based on provider format"""
        if isinstance(chunk, dict):
            return chunk.get("content", "")
        elif isinstance(chunk, str):
            return chunk
        else:
            return str(chunk)
    
    async def _broadcast_thinking_update(self, status: str, content: str):
        """Broadcast thinking process updates"""
        if hasattr(self, 'agui_broadcaster') and self.agui_broadcaster:
            await self.agui_broadcaster.broadcast_thinking_update(
                task_id=self.task_id,
                agent_id=self.agent_id,
                status=status,
                content=content
            )
    
    async def _broadcast_tool_stream_update(
        self, 
        tool_call_id: str, 
        status: str, 
        tool_name: str, 
        arguments: Optional[Dict] = None
    ):
        """Broadcast tool call streaming updates"""
        if hasattr(self, 'agui_broadcaster') and self.agui_broadcaster:
            await self.agui_broadcaster.broadcast_tool_stream_update(
                task_id=self.task_id,
                agent_id=self.agent_id,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                status=status,
                arguments=arguments
            )