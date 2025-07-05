"""
Module: global_supervisor_v2
Purpose: Enhanced Global Supervisor with tool-based architecture and user communication
Dependencies: SupervisorAgent, team supervisor tools
Used By: Main ATLAS system entry point
"""

import asyncio
import time
import uuid
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .supervisor_agent import SupervisorAgent, SupervisorState
from .base import Task, TaskResult, AgentStatus
from ..agui.handlers import AGUIEventBroadcaster
from ..database.chat_manager import chat_manager

logger = logging.getLogger(__name__)


# Tool Functions for Team Supervisors
async def call_research_team(
    task_description: str,
    priority: str = "medium",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Call Research Team Supervisor for information gathering.
    This tool instantiates and runs the Research Team Supervisor.
    """
    # TODO: Import and instantiate actual ResearchTeamSupervisor
    # For now, return simulated response
    logger.info(f"Calling Research Team with task: {task_description[:50]}...")
    
    # Simulate team execution
    await asyncio.sleep(1)  # Simulate processing
    
    return {
        "tool_name": "research_team",
        "status": "complete",
        "findings": {
            "summary": f"Research completed for: {task_description}",
            "key_points": [
                "Finding 1: Relevant research data",
                "Finding 2: Supporting evidence",
                "Finding 3: Additional context"
            ],
            "sources": ["source1.com", "source2.org"],
            "confidence": 0.85
        },
        "metadata": {
            "workers_used": ["web_researcher", "document_analyst"],
            "processing_time": "45s",
            "tokens_used": 1500
        }
    }


async def call_analysis_team(
    task_description: str,
    analysis_type: Optional[str] = None,
    data_sources: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Call Analysis Team Supervisor for data analysis and insights.
    This tool instantiates and runs the Analysis Team Supervisor.
    """
    logger.info(f"Calling Analysis Team for {analysis_type or 'general'} analysis")
    
    # TODO: Import and instantiate actual AnalysisTeamSupervisor
    await asyncio.sleep(1)
    
    return {
        "tool_name": "analysis_team",
        "status": "complete",
        "findings": {
            "analysis_type": analysis_type or "comprehensive",
            "insights": [
                "Insight 1: Data trend analysis",
                "Insight 2: Strategic implications",
                "Insight 3: Risk assessment"
            ],
            "recommendations": [
                "Recommendation 1",
                "Recommendation 2"
            ],
            "confidence": 0.9
        },
        "metadata": {
            "workers_used": ["data_analyst", "strategic_analyst"],
            "data_points_analyzed": 150,
            "processing_time": "60s"
        }
    }


async def call_writing_team(
    task_description: str,
    content_type: Optional[str] = "report",
    tone: Optional[str] = "formal",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Call Writing Team Supervisor for content generation.
    This tool instantiates and runs the Writing Team Supervisor.
    """
    logger.info(f"Calling Writing Team to create {content_type}")
    
    # TODO: Import and instantiate actual WritingTeamSupervisor
    await asyncio.sleep(1)
    
    return {
        "tool_name": "writing_team",
        "status": "complete",
        "findings": {
            "content_type": content_type,
            "draft": f"# {task_description}\n\nThis is a professionally written {content_type}...",
            "word_count": 500,
            "sections": ["Introduction", "Main Body", "Conclusion"],
            "tone_analysis": tone
        },
        "metadata": {
            "workers_used": ["content_writer", "editor"],
            "revisions": 2,
            "processing_time": "90s"
        }
    }


async def call_rating_team(
    task_description: str,
    evaluation_criteria: Optional[List[str]] = None,
    content_to_review: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Call Rating Team Supervisor for quality assurance.
    This tool instantiates and runs the Rating Team Supervisor.
    """
    logger.info(f"Calling Rating Team for quality review")
    
    # TODO: Import and instantiate actual RatingTeamSupervisor
    await asyncio.sleep(0.5)
    
    return {
        "tool_name": "rating_team",
        "status": "complete",
        "findings": {
            "overall_rating": 8.5,
            "criteria_scores": {
                "accuracy": 9.0,
                "completeness": 8.0,
                "clarity": 8.5,
                "formatting": 9.0
            },
            "feedback": [
                "Strong analysis with good evidence",
                "Consider adding more specific examples",
                "Excellent structure and flow"
            ],
            "approval": True
        },
        "metadata": {
            "workers_used": ["quality_reviewer", "fact_checker"],
            "checks_performed": 15,
            "processing_time": "30s"
        }
    }


# User Communication Tool
async def respond_to_user(
    message: str,
    message_type: str = "update",
    include_status: bool = True,
    request_input: bool = False,
    options: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send a response to the user through the chat interface.
    This tool enables continuous communication and human-in-the-loop interaction.
    
    Args:
        message: The message to send to the user
        message_type: Type of message (update, question, result, error)
        include_status: Whether to include current task status
        request_input: Whether to request user input
        options: List of options for user to choose from
        context: Additional context for the message
    """
    logger.info(f"Sending {message_type} message to user")
    
    # Get current task context if available
    task_id = context.get("task_id") if context else None
    
    # Prepare response structure
    response_data = {
        "tool_name": "respond_to_user",
        "message": message,
        "message_type": message_type,
        "timestamp": datetime.now().isoformat(),
        "requires_response": request_input
    }
    
    if include_status and task_id:
        response_data["task_status"] = {
            "task_id": task_id,
            "phase": context.get("current_phase", "processing"),
            "progress": context.get("progress", 0)
        }
    
    if options:
        response_data["options"] = options
    
    # If we have a broadcaster, send through AG-UI
    if context and "agui_broadcaster" in context:
        broadcaster = context["agui_broadcaster"]
        await broadcaster.broadcast_dialogue_update(
            task_id=task_id or "global",
            agent_id="global_supervisor",
            message_id=str(uuid.uuid4()),
            direction="output",
            content={
                "type": "text",
                "data": message,
                "metadata": response_data
            },
            sender="global_supervisor"
        )
    
    # Save to chat history if we have a session
    if task_id and context.get("chat_session_id"):
        await chat_manager.save_message(
            session_id=context["chat_session_id"],
            message_type="agent",
            content=message,
            agent_id="global_supervisor",
            metadata=response_data
        )
    
    return response_data


class GlobalSupervisorV2(SupervisorAgent):
    """
    Enhanced Global Supervisor with parallel tool execution and user communication.
    
    Key features:
    - Calls multiple team supervisors in parallel
    - Communicates with user throughout execution
    - Supports human-in-the-loop interaction
    - Synthesizes results from all teams
    """
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        agui_broadcaster: Optional[AGUIEventBroadcaster] = None,
        mlflow_tracker: Optional[Any] = None,
        chat_session_id: Optional[str] = None
    ):
        # Define all subordinate tools
        subordinate_tools = [
            call_research_team,
            call_analysis_team,
            call_writing_team,
            call_rating_team,
            respond_to_user
        ]
        
        super().__init__(
            agent_id="global_supervisor_v2",
            agent_type="Global Supervisor V2",
            subordinate_tools=subordinate_tools,
            task_id=task_id,
            agui_broadcaster=agui_broadcaster,
            mlflow_tracker=mlflow_tracker
        )
        
        self.chat_session_id = chat_session_id
        self.user_context = {
            "task_id": task_id,
            "agui_broadcaster": agui_broadcaster,
            "chat_session_id": chat_session_id
        }
        
        logger.info(f"Initialized Global Supervisor V2 with {len(subordinate_tools)} tools")
    
    async def process_task(self, task: Task) -> TaskResult:
        """
        Process task with enhanced user communication.
        """
        start_time = time.time()
        
        try:
            # First, acknowledge the task to the user immediately
            await respond_to_user(
                message=f"I've received your request: {task.description}\n\nLet me analyze this and coordinate the appropriate teams.",
                message_type="update",
                include_status=True,
                context={**self.user_context, "current_phase": "initialization", "progress": 0}
            )
            
            # Execute with tools (this will handle the LangGraph workflow)
            result = await self.execute_with_tools(
                task_description=task.description,
                requirements=task.context
            )
            
            # Send final response to user
            if result["success"]:
                await respond_to_user(
                    message=f"Task completed successfully!\n\n{result['content']}",
                    message_type="result",
                    include_status=True,
                    context={**self.user_context, "current_phase": "completed", "progress": 100}
                )
            else:
                await respond_to_user(
                    message=f"I encountered an issue: {result['content']}\n\nWould you like me to try a different approach?",
                    message_type="error",
                    request_input=True,
                    options=["Retry", "Modify approach", "Cancel"],
                    context=self.user_context
                )
            
            # Return task result
            processing_time = time.time() - start_time
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="global_coordination",
                content=result,
                success=result["success"],
                processing_time=processing_time,
                metadata={
                    "tool_calls_made": result.get("tool_calls_made", 0),
                    "iterations": result.get("iterations", 0),
                    "user_interactions": 2  # Start and end
                }
            )
            
        except Exception as e:
            logger.error(f"Global Supervisor V2 execution failed: {e}")
            
            # Notify user of error
            await respond_to_user(
                message=f"I encountered an unexpected error: {str(e)}\n\nPlease try again or contact support if the issue persists.",
                message_type="error",
                context=self.user_context
            )
            
            processing_time = time.time() - start_time
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="global_coordination",
                content={"error": str(e)},
                success=False,
                processing_time=processing_time,
                errors=[str(e)]
            )
    
    async def _supervisor_node(self, state: SupervisorState) -> SupervisorState:
        """
        Override supervisor node to add user communication.
        """
        # Check if we should update the user on progress
        if state.iteration_count > 0 and state.completed_tool_results:
            # Summarize progress for user
            teams_complete = len(state.completed_tool_results)
            teams_total = len(state.pending_tool_calls) + teams_complete
            
            progress_message = f"Progress Update: {teams_complete}/{teams_total} teams have completed their work."
            
            # Add specific team results
            for result in state.completed_tool_results[-2:]:  # Last 2 results
                if result.status == "success":
                    progress_message += f"\n✓ {result.tool_call_id.split('_')[0]} team completed successfully"
            
            # Send progress update
            await respond_to_user(
                message=progress_message,
                message_type="update",
                include_status=True,
                context={
                    **self.user_context,
                    "current_phase": "execution",
                    "progress": int((teams_complete / teams_total) * 80)  # 80% for execution
                }
            )
        
        # Call parent implementation
        return await super()._supervisor_node(state)
    
    def _build_initial_reasoning_prompt(self, state: SupervisorState) -> str:
        """
        Override to emphasize user communication in prompts.
        """
        base_prompt = super()._build_initial_reasoning_prompt(state)
        
        return f"""{base_prompt}

IMPORTANT: You have access to the 'respond_to_user' tool. Use it to:
1. Provide progress updates during long-running tasks
2. Ask for clarification if the task is ambiguous
3. Request user preferences when multiple approaches are valid
4. Report any issues that require user attention

Remember to balance efficiency with user communication - don't over-communicate, but keep the user informed of significant progress or decisions."""
    
    async def get_system_prompt(self) -> str:
        """
        Enhanced system prompt with user communication emphasis.
        """
        base_prompt = await super().get_system_prompt()
        
        return f"""{base_prompt}

USER COMMUNICATION GUIDELINES:
- Proactively communicate progress on complex tasks
- Ask for clarification when requirements are ambiguous
- Provide clear, actionable error messages
- Summarize findings in user-friendly language
- Support human-in-the-loop decision making

TOOL USAGE PATTERNS:
- Use parallel execution for independent teams
- Chain dependent operations appropriately
- Always respond to user at task start and completion
- Provide intermediate updates for long-running tasks"""


# asyncio is already imported at the top of the file