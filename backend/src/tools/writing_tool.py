"""
Writing Delegation Tool for ATLAS Supervisor Agent
Delegates writing tasks to writing agents with structured prompts
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Global factory instance (lazy initialization)
_factory = None

def get_factory():
    """Get or create the LettaAgentFactory instance."""
    global _factory
    if _factory is None:
        from src.agents.agent_factory import LettaAgentFactory
        _factory = LettaAgentFactory()
    return _factory

def delegate_writing(context: str, task_description: str, restrictions: str = "") -> Dict[str, Any]:
    """
    Delegate writing task to writing agent using structured XML prompts.

    The supervisor acts as prompt engineer, providing complete context including
    research findings, analysis results, and clear writing tasks. The writing agent
    will have its own isolated planning and todo tools via namespace.

    Args:
        context: Overall goal, completed work (research & analysis), and next steps
        task_description: Specific writing actions to take
        restrictions: Style, format, tone, and content boundaries

    Returns:
        Dictionary with:
        - task_id: Unique identifier for tracking
        - agent_id: Writing agent's ID
        - status: "delegated" or "failed"
        - initial_response: Agent's acknowledgment
        - delegated_at: Timestamp of delegation
    """

    try:
        factory = get_factory()

        # Generate unique task ID
        task_id = f"writing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create or retrieve writing agent
        agent = factory.create_writing_agent(task_id, context)

        # Register isolated tools for this agent
        agent_namespace = f"writing_{agent.id}"

        # Construct XML-structured prompt (supervisor's prompt engineering)
        agent_prompt = f"""<context>
{context}
</context>

<task>
{task_description}
</task>

<restrictions>
{restrictions if restrictions else "No specific restrictions provided."}
</restrictions>"""

        # Send message to agent
        logger.info(f"Delegating writing task {task_id} to agent {agent.id}")
        response = factory.send_message_to_agent(agent.id, agent_prompt)

        return {
            "task_id": task_id,
            "agent_id": agent.id,
            "status": "delegated",
            "delegated_at": datetime.now().isoformat(),
            "initial_response": response,
            "agent_namespace": agent_namespace
        }

    except Exception as e:
        logger.error(f"Failed to delegate writing task: {str(e)}")
        return {
            "task_id": task_id if 'task_id' in locals() else "error",
            "status": "failed",
            "error": str(e),
            "delegated_at": datetime.now().isoformat()
        }

def get_writing_status(agent_id: str) -> Dict[str, Any]:
    """
    Get the current status of a writing agent's task.

    Args:
        agent_id: The writing agent's ID

    Returns:
        Status information from the agent
    """
    try:
        factory = get_factory()

        # Query agent for status
        status_prompt = "What is the current status of your writing task?"
        response = factory.send_message_to_agent(agent_id, status_prompt)

        return {
            "agent_id": agent_id,
            "status": "active",
            "response": response,
            "queried_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get writing status: {str(e)}")
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(e),
            "queried_at": datetime.now().isoformat()
        }