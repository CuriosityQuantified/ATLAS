"""
Module: supervisor_agent
Purpose: Base class for all supervisor agents with parallel tool execution
Dependencies: BaseAgent, LettaAgentMixin, LangGraph
Used By: Global Supervisor, Team Supervisors
"""

from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel
import logging
import asyncio
import time
from datetime import datetime

from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolNode  # TODO: Re-enable when fixing LangGraph integration
# from langgraph.graph.state import CompiledStateGraph  # TODO: Re-enable when fixing LangGraph integration

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
    max_iterations: int = 10


class SupervisorAgent(BaseAgent, SimpleLettaAgentMixin):
    """
    Base class for all supervisor agents.
    
    Key features:
    - Supports multiple parallel tool calls
    - Uses LangGraph for orchestration
    - Maintains state across iterations
    - Can call subordinate agents as tools
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
        
        # Create workflow
        self.workflow = self._create_workflow()
        
        logger.info(f"Initialized {agent_type} with {len(self.subordinate_tools)} subordinate tools")
    
    def _create_workflow(self):
        """Create workflow for tool-based execution"""
        # TODO: Implement full LangGraph integration
        # For now, return a simple workflow simulator
        return None
    
    async def _supervisor_node(self, state: SupervisorState) -> SupervisorState:
        """
        Supervisor reasoning node.
        Decides what tools to call or if task is complete.
        """
        await self.update_status(AgentStatus.PROCESSING, "Analyzing task and planning tool usage")
        
        # Check iteration limit
        if state.iteration_count >= state.max_iterations:
            state.is_complete = True
            state.final_output = "Maximum iterations reached. Returning best available results."
            return state
        
        state.iteration_count += 1
        
        # If we have tool results to process
        if state.completed_tool_results and not state.pending_tool_calls:
            # Analyze results and decide next steps
            analysis_prompt = self._build_result_analysis_prompt(state)
            response = await self.send_to_letta(analysis_prompt)
            
            # Extract any new tool calls
            new_tool_calls = response.get("tool_calls", [])
            if new_tool_calls:
                state.pending_tool_calls = [
                    ToolCall(
                        id=f"call_{state.iteration_count}_{i}",
                        name=tc["name"],
                        arguments=tc.get("arguments", {})
                    )
                    for i, tc in enumerate(new_tool_calls)
                ]
                state.awaiting_tool_results = True
                state.needs_more_tools = True
            else:
                # Check if supervisor thinks task is complete
                if "TASK_COMPLETE" in response.get("content", ""):
                    state.is_complete = True
                    state.final_output = self._extract_final_output(response["content"])
                else:
                    state.needs_more_tools = True
        
        # Initial reasoning about the task
        elif not state.messages:
            reasoning_prompt = self._build_initial_reasoning_prompt(state)
            response = await self.send_to_letta(reasoning_prompt)
            
            state.messages.append(response.get("content", ""))
            
            # Extract tool calls
            tool_calls = response.get("tool_calls", [])
            if tool_calls:
                state.pending_tool_calls = [
                    ToolCall(
                        id=f"call_{state.iteration_count}_{i}",
                        name=tc["name"],
                        arguments=tc.get("arguments", {})
                    )
                    for i, tc in enumerate(tool_calls)
                ]
                state.awaiting_tool_results = True
            else:
                # No tools needed, task might be simple
                state.is_complete = True
                state.final_output = response.get("content", "No tools required for this task.")
        
        return state
    
    def _route_supervisor(self, state: SupervisorState) -> str:
        """Route based on supervisor state"""
        if state.pending_tool_calls and state.awaiting_tool_results:
            return "execute_tools"
        elif state.completed_tool_results and not state.is_complete:
            return "process_results"
        else:
            return "complete"
    
    def _build_initial_reasoning_prompt(self, state: SupervisorState) -> str:
        """Build prompt for initial task analysis"""
        tools_desc = "\n".join([
            f"- {tool.__name__}: {tool.__doc__}"
            for tool in self.subordinate_tools
        ])
        
        return f"""You are a supervisor agent responsible for coordinating subordinate agents.

Task: {state.task_description}

Available tools (you can call multiple in parallel):
{tools_desc}

Analyze this task and determine:
1. Which tools need to be called
2. What information each tool should gather
3. Whether tools can be called in parallel

You can make multiple tool calls at once for parallel execution.
Format tool calls as instructed.

If the task is simple and doesn't require tools, respond with your direct answer and include "TASK_COMPLETE" in your response."""
    
    def _build_result_analysis_prompt(self, state: SupervisorState) -> str:
        """Build prompt for analyzing tool results"""
        results_summary = "\n".join([
            f"Tool: {result.tool_call_id}\nStatus: {result.status}\nContent: {result.content}\n"
            for result in state.completed_tool_results[-5:]  # Last 5 results
        ])
        
        return f"""You are analyzing results from tool executions.

Original task: {state.task_description}

Recent tool results:
{results_summary}

Based on these results:
1. Do you need to call more tools? If yes, specify which ones.
2. Is the task complete? If yes, synthesize the final answer and include "TASK_COMPLETE" in your response.
3. Are there any issues that need addressing?

Remember, you can call multiple tools in parallel if needed."""
    
    def _extract_final_output(self, content: str) -> str:
        """Extract final output from supervisor response"""
        # Remove TASK_COMPLETE marker and clean up
        output = content.replace("TASK_COMPLETE", "").strip()
        return output
    
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
                # Should not happen
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
            logger.info(f"Broadcasting tool call initiated: {tool_call.name} (id: {tool_call.id})")
            # Broadcast to the regular task ID that frontend connects to
            await self.agui_broadcaster.broadcast_tool_call_initiated(
                task_id=self.task_id if self.task_id else "unknown",
                agent_id=self.agent_id,
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                arguments=tool_call.arguments or {}
            )
        else:
            logger.warning(f"No agui_broadcaster available for agent {self.agent_id}")
        
        try:
            # Broadcast tool call executing
            if hasattr(self, 'agui_broadcaster') and self.agui_broadcaster:
                await self.agui_broadcaster.broadcast_tool_call_executing(
                    task_id=self.task_id if self.task_id else "unknown",
                    agent_id=self.agent_id,
                    tool_call_id=tool_call.id,
                    tool_name=tool_call.name
                )
            
            # Get structure service
            structure_service = get_structure_service()
            
            # Get schema for this tool
            tool_schema = TOOL_SCHEMAS.get(tool_call.name, {})
            
            # Structure the arguments using Osmosis-Structure
            if tool_schema and tool_call.arguments:
                structured_args = await structure_service.structure_agent_output(
                    str(tool_call.arguments),
                    tool_schema,
                    tool_call.name
                )
                logger.debug(f"Structured arguments for {tool_call.name}: {structured_args}")
            else:
                structured_args = tool_call.arguments
            
            # For respond_to_user, inject the broadcaster context
            if tool_call.name == "respond_to_user" and hasattr(self, 'agui_broadcaster'):
                if "context" not in structured_args:
                    structured_args["context"] = {}
                structured_args["context"]["agui_broadcaster"] = self.agui_broadcaster
                structured_args["context"]["task_id"] = self.task_id
                structured_args["context"]["chat_session_id"] = getattr(self, 'chat_session_id', None)
            
            # Call the tool with structured arguments
            result = await tool(**structured_args)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Broadcast tool call completed
            if hasattr(self, 'agui_broadcaster') and self.agui_broadcaster:
                logger.info(f"Broadcasting tool call completed: {tool_call.name} (id: {tool_call.id})")
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
                    "execution_time": datetime.now().isoformat(),
                    "execution_time_ms": execution_time_ms,
                    "structured": bool(tool_schema)
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
    
    async def execute_with_tools(
        self,
        task_description: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute task using subordinate tools with parallel support.
        
        This is the main entry point for supervisor execution.
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
        
        # Run simple workflow without LangGraph for now
        try:
            # Simple execution loop
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
                    "parallel_executions": self._count_parallel_executions(state)
                }
            }
        except Exception as e:
            logger.error(f"Supervisor execution failed: {e}")
            return {
                "success": False,
                "content": f"Execution failed: {str(e)}",
                "tool_calls_made": 0,
                "iterations": 0
            }
    
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
    
    def _count_parallel_executions(self, state: SupervisorState) -> int:
        """Count how many times tools were executed in parallel"""
        # Group by iteration to see parallel calls
        parallel_count = 0
        current_iteration = None
        iteration_calls = 0
        
        for result in state.completed_tool_results:
            iteration = result.tool_call_id.split('_')[1]
            if iteration != current_iteration:
                if iteration_calls > 1:
                    parallel_count += 1
                current_iteration = iteration
                iteration_calls = 1
            else:
                iteration_calls += 1
        
        # Check last iteration
        if iteration_calls > 1:
            parallel_count += 1
            
        return parallel_count
    
    async def process_task(self, task: Task) -> TaskResult:
        """
        Process task using subordinate tools.
        This implements the abstract method from BaseAgent.
        """
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
        base_prompt = await super().get_system_prompt()
        
        return f"""{base_prompt}

SUPERVISOR AGENT CAPABILITIES:
- Coordinate multiple subordinate agents/tools
- Execute tools in parallel for efficiency
- Analyze results and make decisions
- Iterate until task completion
- Synthesize findings from multiple sources

EXECUTION PATTERN:
1. Analyze the task requirements
2. Identify which tools to use (can be multiple)
3. Execute tools in parallel when possible
4. Analyze results and determine next steps
5. Repeat until task is complete
6. Synthesize final answer from all results

Remember: You can and should call multiple tools in parallel when it makes sense."""