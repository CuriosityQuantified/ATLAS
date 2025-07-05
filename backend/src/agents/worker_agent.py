"""
Module: worker_agent
Purpose: Base class for all worker agents with tool-based ReAct loop
Dependencies: BaseAgent, LettaAgentMixin
Used By: All worker agents (Web Researcher, Document Analyst, etc.)
"""

from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel
import logging
from datetime import datetime

from .base import BaseAgent, Task, TaskResult, AgentStatus
from .letta_simple import SimpleLettaAgentMixin
from ..agui.handlers import AGUIEventBroadcaster

logger = logging.getLogger(__name__)


class ReActStep(BaseModel):
    """Model for a single ReAct step"""
    step_number: int
    thought: str = ""  # Default empty string
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    is_complete: bool = False
    final_answer: Optional[str] = None


class WorkerAgent(BaseAgent, SimpleLettaAgentMixin):
    """
    Base class for all worker agents.
    
    Key features:
    - Uses ReAct (Reasoning-Action) loop
    - All operations are tool-based (including reasoning)
    - Returns structured results to supervisors
    - Operates until task completion or max iterations
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        external_tools: List[Callable] = None,
        max_iterations: int = 5,
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
        
        # Worker configuration
        self.max_iterations = max_iterations
        self.external_tools = external_tools or []
        
        # Create tool registry including reasoning tool
        self.tool_registry = {
            "reason_about_task": self._reason_about_task_tool,
            "return_findings": self._return_findings_tool
        }
        
        # Add external tools to registry
        for tool in self.external_tools:
            self.tool_registry[tool.__name__] = tool
        
        # All available tools for Letta
        self.all_tools = list(self.tool_registry.values())
        
        logger.info(f"Initialized {agent_type} worker with {len(self.all_tools)} tools")
    
    async def _reason_about_task_tool(
        self,
        task_description: str,
        context: Dict[str, Any],
        history: List[ReActStep]
    ) -> Dict[str, Any]:
        """
        Tool for reasoning about the task (ReAct Thought step).
        This makes reasoning itself a tool-based operation.
        
        Returns:
            Next action to take and reasoning
        """
        history_summary = self._summarize_history(history)
        
        reasoning_prompt = f"""You are reasoning about a task using the ReAct pattern.

Task: {task_description}

Context: {context}

History of previous steps:
{history_summary}

Available actions:
{self._get_available_actions()}

Think step-by-step:
1. What have we learned so far?
2. What information is still needed?
3. What should be the next action?

Provide your reasoning and the next action to take.
If the task is complete, indicate so in your reasoning."""

        response = await self.send_to_letta(reasoning_prompt)
        
        # Parse reasoning and determine next action
        content = response.get("content", "")
        
        # Check if task is complete
        if "task is complete" in content.lower() or "final answer" in content.lower():
            return {
                "thought": content,
                "is_complete": True,
                "next_action": "return_findings",
                "confidence": 0.9
            }
        
        # Extract next action from reasoning
        next_action = self._extract_next_action(content, response.get("tool_calls", []))
        
        return {
            "thought": content,
            "is_complete": False,
            "next_action": next_action.get("name", "none"),
            "action_args": next_action.get("args", {}),
            "confidence": 0.7
        }
    
    async def _return_findings_tool(
        self,
        task_description: str,
        findings: Dict[str, Any],
        history: List[ReActStep],
        confidence: float = 0.8
    ) -> Dict[str, Any]:
        """
        Tool for returning final findings to supervisor.
        This is how workers communicate results back up the hierarchy.
        """
        # Synthesize findings from history
        synthesis_prompt = f"""Synthesize the findings from this task execution.

Task: {task_description}

Collected findings: {findings}

Execution history:
{self._summarize_history(history)}

Create a comprehensive summary of:
1. Key findings and insights
2. Evidence supporting the findings
3. Any limitations or caveats
4. Recommendations or next steps

Be concise but thorough."""

        response = await self.send_to_letta(synthesis_prompt)
        
        return {
            "task_id": self.task_id,
            "worker_id": self.agent_id,
            "task_description": task_description,
            "findings": response.get("content", ""),
            "structured_data": findings,
            "confidence": confidence,
            "iterations_used": len(history),
            "metadata": {
                "worker_type": self.agent_type,
                "tools_used": self._get_tools_used(history),
                "execution_time": datetime.now().isoformat()
            }
        }
    
    async def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute task using ReAct loop with tools.
        
        This is the main entry point for worker execution.
        """
        await self.update_status(AgentStatus.PROCESSING, "Starting ReAct execution")
        
        # Initialize Letta with all tools
        await self.initialize_letta_agent(tools=[
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": getattr(tool, "__doc__", f"Execute {tool_name}"),
                    "parameters": self._extract_tool_parameters(tool)
                }
            }
            for tool_name, tool in self.tool_registry.items()
        ])
        
        # Initialize execution state
        history: List[ReActStep] = []
        context = context or {}
        findings = {}
        
        # ReAct loop
        for iteration in range(self.max_iterations):
            step = ReActStep(step_number=iteration + 1)
            
            # Reason about task
            reasoning_result = await self.tool_registry["reason_about_task"](
                task_description=task_description,
                context=context,
                history=history
            )
            
            step.thought = reasoning_result["thought"]
            step.is_complete = reasoning_result["is_complete"]
            
            if step.is_complete:
                # Task complete, return findings
                step.action = "return_findings"
                step.final_answer = reasoning_result.get("thought", "Task completed")
                history.append(step)
                
                # Use return_findings tool
                final_result = await self.tool_registry["return_findings"](
                    task_description=task_description,
                    findings=findings,
                    history=history,
                    confidence=reasoning_result.get("confidence", 0.8)
                )
                
                await self.update_status(AgentStatus.COMPLETED, "Task execution complete")
                return final_result
            
            # Execute action
            action_name = reasoning_result["next_action"]
            action_args = reasoning_result.get("action_args", {})
            
            step.action = action_name
            step.action_input = action_args
            
            if action_name in self.tool_registry:
                try:
                    # Execute the tool
                    tool_result = await self.tool_registry[action_name](**action_args)
                    step.observation = str(tool_result)
                    
                    # Update findings
                    findings[f"step_{iteration + 1}"] = tool_result
                    
                except Exception as e:
                    step.observation = f"Error executing {action_name}: {str(e)}"
                    logger.error(f"Tool execution failed: {e}")
            else:
                step.observation = f"Unknown action: {action_name}"
            
            history.append(step)
        
        # Max iterations reached
        await self.update_status(AgentStatus.COMPLETED, "Max iterations reached")
        
        # Return best available results
        return await self.tool_registry["return_findings"](
            task_description=task_description,
            findings=findings,
            history=history,
            confidence=0.6  # Lower confidence due to incomplete execution
        )
    
    def _summarize_history(self, history: List[ReActStep]) -> str:
        """Create a summary of ReAct history"""
        if not history:
            return "No previous steps."
        
        summary = []
        for step in history[-3:]:  # Last 3 steps
            summary.append(f"Step {step.step_number}:")
            summary.append(f"  Thought: {step.thought[:100]}...")
            if step.action:
                summary.append(f"  Action: {step.action}")
            if step.observation:
                summary.append(f"  Observation: {step.observation[:100]}...")
        
        return "\n".join(summary)
    
    def _get_available_actions(self) -> str:
        """Get list of available actions/tools"""
        actions = []
        for name, tool in self.tool_registry.items():
            if name not in ["reason_about_task", "return_findings"]:
                doc = getattr(tool, "__doc__", "No description")
                actions.append(f"- {name}: {doc.split('.')[0]}")
        return "\n".join(actions)
    
    def _extract_next_action(self, reasoning: str, tool_calls: List[Dict]) -> Dict[str, Any]:
        """Extract next action from reasoning or tool calls"""
        # First check explicit tool calls
        if tool_calls:
            first_call = tool_calls[0]
            return {
                "name": first_call.get("name", ""),
                "args": first_call.get("arguments", {})
            }
        
        # Try to parse from reasoning text
        reasoning_lower = reasoning.lower()
        
        # Look for action indicators
        for tool_name in self.tool_registry:
            if tool_name in reasoning_lower and tool_name not in ["reason_about_task", "return_findings"]:
                return {"name": tool_name, "args": {}}
        
        # Default: need more reasoning
        return {"name": "reason_about_task", "args": {}}
    
    def _get_tools_used(self, history: List[ReActStep]) -> List[str]:
        """Extract list of tools used during execution"""
        tools_used = set()
        for step in history:
            if step.action and step.action != "reason_about_task":
                tools_used.add(step.action)
        return list(tools_used)
    
    def _extract_tool_parameters(self, tool: Callable) -> Dict[str, Any]:
        """Extract parameters from tool function"""
        import inspect
        sig = inspect.signature(tool)
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'cls']:
                continue
            
            param_info = {"type": "string"}
            
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
            
            if param.default == param.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    async def process_task(self, task: Task) -> TaskResult:
        """
        Process task using ReAct loop.
        This implements the abstract method from BaseAgent.
        """
        result = await self.execute_task(
            task_description=task.description,
            context=task.context
        )
        
        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            result_type="worker_execution",
            content=result,
            success=result.get("findings") is not None,
            processing_time=result.get("metadata", {}).get("execution_time", 0),
            metadata=result.get("metadata", {})
        )
    
    async def get_system_prompt(self) -> str:
        """Get worker-specific system prompt"""
        base_prompt = await super().get_system_prompt()
        
        return f"""{base_prompt}

WORKER AGENT CAPABILITIES:
- Execute specific tasks using ReAct pattern
- Use tools for ALL operations (including reasoning)
- Gather information systematically
- Return structured findings to supervisors
- Operate autonomously until task completion

REACT PATTERN:
1. Reason: Think about the task and current state
2. Act: Choose and execute appropriate tool
3. Observe: Analyze tool results
4. Repeat: Continue until task complete

Remember: Every operation must be a tool call, including reasoning and returning results."""