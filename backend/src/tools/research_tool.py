"""
Research Delegation Tool for ATLAS Supervisor Agent
Delegates research tasks to research agents with structured prompts
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

def delegate_research(context: str, task_description: str, restrictions: str = "") -> Dict[str, Any]:
    """
    Delegate research task to research agent using structured XML prompts.

    The supervisor acts as prompt engineer, providing complete context and clear tasks.
    The research agent will have its own isolated planning and todo tools via namespace.

    Args:
        context: Overall goal, completed work, and next steps
        task_description: Specific research actions to take
        restrictions: Boundaries and requirements for the research

    Returns:
        Dictionary with:
        - task_id: Unique identifier for tracking
        - agent_id: Research agent's ID
        - status: "delegated" or "failed"
        - initial_response: Agent's acknowledgment
        - delegated_at: Timestamp of delegation
    """

    try:
        factory = get_factory()

        # Generate unique task ID
        task_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create or retrieve research agent
        agent = factory.create_research_agent(task_id, context)

        # Register isolated tools for this agent
        # Note: This would normally be done through Letta's tool registration API
        # For now, we'll rely on the agent factory to handle this
        agent_namespace = f"research_{agent.id}"

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
        logger.info(f"Delegating research task {task_id} to agent {agent.id}")
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
        logger.error(f"Failed to delegate research task: {str(e)}")
        return {
            "task_id": task_id if 'task_id' in locals() else "error",
            "status": "failed",
            "error": str(e),
            "delegated_at": datetime.now().isoformat()
        }

def get_research_status(agent_id: str) -> Dict[str, Any]:
    """
    Get the current status of a research agent's task.

    Args:
        agent_id: The research agent's ID

    Returns:
        Status information from the agent
    """
    try:
        factory = get_factory()

        # Query agent for status
        status_prompt = "What is the current status of your research task?"
        response = factory.send_message_to_agent(agent_id, status_prompt)

        return {
            "agent_id": agent_id,
            "status": "active",
            "response": response,
            "queried_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get research status: {str(e)}")
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(e),
            "queried_at": datetime.now().isoformat()
        }