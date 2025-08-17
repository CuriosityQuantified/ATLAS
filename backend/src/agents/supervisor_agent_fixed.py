"""
Module: supervisor_agent_fixed
Purpose: Fixed supervisor agent with better streaming and tool parsing
Dependencies: BaseAgent, LettaAgentMixin, StreamingMixin
Used By: Global Supervisor, Team Supervisors
"""

from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel
import logging
import asyncio
import time
from datetime import datetime

from .base import BaseAgent, Task, TaskResult, AgentStatus
from .letta_simple import SimpleLettaAgentMixin
from ..agui.handlers import AGUIEventBroadcaster
from .structure_service_hybrid import get_structure_service, TOOL_SCHEMAS

logger = logging.getLogger(__name__)


class ToolCall(BaseModel):
    """Model for a tool call request"""
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Model for a tool execution result"""
    tool_call_id: str
    status: str  # "success" or "error"
    content: Any
    metadata: Optional[Dict[str, Any]] = None


class SupervisorState(BaseModel):
    """State for supervisor execution with parallel tool support"""
    task_id: str
    task_description: str
    messages: List[str] = []
    pending_tool_calls: List[ToolCall] = []
    active_tool_calls: Dict[str, ToolCall] = {}
    completed_tool_results: List[ToolResult] = []
    awaiting_tool_results: bool = False
    needs_more_tools: bool = False
    is_complete: bool = False
    final_output: str = ""
    iteration_count: int = 0
    max_iterations: int = 3  # Reduced from 10 to prevent loops


class SupervisorAgent(BaseAgent, SimpleLettaAgentMixin):
    """
    Fixed supervisor agent with better streaming and error handling.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        subordinate_tools: List[Callable] = None,
        task_id: Optional[str] = None,
        agui_broadcaster: Optional[AGUIEventBroadcaster] = None,
        mlflow_tracker: Optional[Any] = None
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            task_id=task_id,
            agui_broadcaster=agui_broadcaster,
            mlflow_tracker=mlflow_tracker
        )
        
        # Initialize SimpleLetta
        self._init_simple_letta()
        
        # Store subordinate tools
        self.subordinate_tools = subordinate_tools or []
        self.tool_registry = {tool.__name__: tool for tool in self.subordinate_tools}
        
        logger.info(f"Initialized {agent_type} with {len(self.subordinate_tools)} subordinate tools")
    
    async def _supervisor_node(self, state: SupervisorState) -> SupervisorState:
        """
        Supervisor reasoning node with immediate response.
        """
        await self.update_status(AgentStatus.PROCESSING, "Analyzing task")
        
        # Check iteration limit
        if state.iteration_count >= state.max_iterations:
            state.is_complete = True
            state.final_output = "I've analyzed your request. Let me help you with that."
            return state
        
        state.iteration_count += 1
        
        # For simple greetings, respond immediately
        task_lower = state.task_description.lower()
        if any(greeting in task_lower for greeting in ["hi", "hello", "hey", "yo"]):
            state.is_complete = True
            state.final_output = "Hello! I'm here to help. What would you like me to assist you with today?"
            return state
        
        # Otherwise, use tools
        if not state.messages:
            reasoning_prompt = self._build_initial_reasoning_prompt(state)
            response = await self.send_to_letta(reasoning_prompt)
            
            state.messages.append(response.get("content", ""))
            
            # Extract tool calls more carefully
            tool_calls = response.get("tool_calls", [])
            valid_tool_calls = []
            
            for tc in tool_calls:
                # Validate tool call structure
                if isinstance(tc, dict) and "name" in tc:
                    # Clean up arguments
                    args = tc.get("arguments", {})
                    if isinstance(args, dict) and "raw" in args:
                        # Skip malformed arguments
                        if args["raw"] == "{":
                            continue
                    
                    valid_tool_calls.append(ToolCall(
                        id=f"call_{state.iteration_count}_{len(valid_tool_calls)}",
                        name=tc["name"],
                        arguments=args if isinstance(args, dict) else {}
                    ))
            
            if valid_tool_calls:
                state.pending_tool_calls = valid_tool_calls
                state.awaiting_tool_results = True
            else:
                # No valid tools, complete the task
                state.is_complete = True
                state.final_output = response.get("content", "I'll help you with your request.")
        
        return state
    
    async def execute_with_tools(
        self,
        task_description: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute task with immediate user feedback.
        """
        # Initialize Letta with supervisor tools
        await self.initialize_letta_agent(tools=[
            {
                "type": "function",
                "function": {
                    "name": tool.__name__,
                    "description": tool.__doc__ or f"Call {tool.__name__}",
                    "parameters": self._extract_tool_parameters(tool)
                }
            }
            for tool in self.subordinate_tools
        ])
        
        # Create initial state
        initial_state = SupervisorState(
            task_id=self.task_id or f"supervisor_{self.agent_id}",
            task_description=task_description
        )
        
        # Run simple workflow
        try:
            state = initial_state
            
            while not state.is_complete and state.iteration_count < state.max_iterations:
                # Run supervisor reasoning
                state = await self._supervisor_node(state)
                
                # Execute any pending tools
                if state.pending_tool_calls:
                    results = await self._execute_tools_parallel(state.pending_tool_calls)
                    state.completed_tool_results.extend(results)
                    state.pending_tool_calls = []
                    state.awaiting_tool_results = False
            
            return {
                "success": state.is_complete,
                "content": state.final_output,
                "tool_calls_made": len(state.completed_tool_results),
                "iterations": state.iteration_count,
                "metadata": {
                    "supervisor_id": self.agent_id,
                    "parallel_executions": 0
                }
            }
        except Exception as e:
            logger.error(f"Supervisor execution failed: {e}")
            return {
                "success": False,
                "content": f"I encountered an error: {str(e)}",
                "tool_calls_made": 0,
                "iterations": 0
            }
    
    async def _execute_tools_parallel(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """Execute multiple tool calls in parallel"""
        tasks = []
        
        for tool_call in tool_calls:
            if tool_call.name in self.tool_registry:
                tool = self.tool_registry[tool_call.name]
                task = asyncio.create_task(self._execute_single_tool(tool_call, tool))
                tasks.append(task)
            else:
                # Create error result for unknown tool
                tasks.append(asyncio.create_task(self._create_error_result(
                    tool_call,
                    f"Unknown tool: {tool_call.name}"
                )))
        
        # Wait for all tools to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert results to ToolResult objects
        tool_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tool_results.append(ToolResult(
                    tool_call_id=tool_calls[i].id,
                    status="error",
                    content=str(result)
                ))
            elif isinstance(result, ToolResult):
                tool_results.append(result)
            else:
                tool_results.append(ToolResult(
                    tool_call_id=tool_calls[i].id,
                    status="error",
                    content="Invalid result type"
                ))
        
        return tool_results
    
    async def _execute_single_tool(self, tool_call: ToolCall, tool: Callable) -> ToolResult:
        """Execute a single tool call"""
        start_time = time.time()
        
        # Broadcast tool call initiated
        if hasattr(self, 'agui_broadcaster') and self.agui_broadcaster:
            await self.agui_broadcaster.broadcast_tool_call_initiated(
                task_id=self.task_id if self.task_id else "unknown",
                agent_id=self.agent_id,
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                arguments=tool_call.arguments or {}
            )
        
        try:
            # Execute tool
            result = await tool(**tool_call.arguments)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Broadcast tool call completed
            if hasattr(self, 'agui_broadcaster') and self.agui_broadcaster:
                await self.agui_broadcaster.broadcast_tool_call_completed(
                    task_id=self.task_id if self.task_id else "unknown",
                    agent_id=self.agent_id,
                    tool_call_id=tool_call.id,
                    tool_name=tool_call.name,
                    result=result,
                    execution_time_ms=execution_time_ms
                )
            
            return ToolResult(
                tool_call_id=tool_call.id,
                status="success",
                content=result,
                metadata={
                    "tool_name": tool_call.name,
                    "execution_time_ms": execution_time_ms
                }
            )
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_call.name}: {e}")
            
            # Broadcast tool call failed
            if hasattr(self, 'agui_broadcaster') and self.agui_broadcaster:
                await self.agui_broadcaster.broadcast_tool_call_failed(
                    task_id=self.task_id if self.task_id else "unknown",
                    agent_id=self.agent_id,
                    tool_call_id=tool_call.id,
                    tool_name=tool_call.name,
                    error_message=str(e)
                )
            
            return ToolResult(
                tool_call_id=tool_call.id,
                status="error",
                content=f"Tool execution failed: {str(e)}"
            )
    
    async def _create_error_result(self, tool_call: ToolCall, error_message: str) -> ToolResult:
        """Create an error result for a tool call"""
        return ToolResult(
            tool_call_id=tool_call.id,
            status="error",
            content=error_message
        )
    
    def _build_initial_reasoning_prompt(self, state: SupervisorState) -> str:
        """Build prompt for initial task analysis"""
        tools_desc = "\n".join([
            f"- {tool.__name__}: {tool.__doc__}"
            for tool in self.subordinate_tools
        ])
        
        return f"""You are a supervisor agent responsible for coordinating subordinate agents.

Task: {state.task_description}

Available tools:
{tools_desc}

If this is a simple greeting (hi, hello, hey, etc), respond directly without using tools.
Otherwise, analyze the task and determine which tools to use.

Format tool calls as:
TOOL_CALL: tool_name
ARGUMENTS: {{"param1": "value1", "param2": "value2"}}"""
    
    def _extract_tool_parameters(self, tool: Callable) -> Dict[str, Any]:
        """Extract parameters from tool function signature"""
        import inspect
        sig = inspect.signature(tool)
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'cls']:
                continue
                
            param_info = {"type": "string"}  # Default type
            
            # Try to infer type from annotation
            if param.annotation != param.empty:
                if param.annotation == str:
                    param_info["type"] = "string"
                elif param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif param.annotation == dict or param.annotation == Dict:
                    param_info["type"] = "object"
                elif param.annotation == list or param.annotation == List:
                    param_info["type"] = "array"
            
            properties[param_name] = param_info
            
            # Check if required
            if param.default == param.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process task using subordinate tools"""
        result = await self.execute_with_tools(
            task_description=task.description,
            requirements=task.context
        )
        
        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            result_type="supervisor_coordination",
            content=result,
            success=result["success"],
            processing_time=result.get("processing_time", 0),
            metadata=result.get("metadata", {})
        )
    
    async def get_system_prompt(self) -> str:
        """Get supervisor-specific system prompt"""
        return """You are a helpful supervisor agent that coordinates tasks.
For simple greetings, respond directly and warmly.
For complex tasks, use your available tools to help the user."""