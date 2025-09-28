"""
Supervisor Agent for ATLAS Multi-Agent System

The Supervisor class orchestrates task execution using tool-based architecture,
delegating work to specialized agents while maintaining overall coordination.
"""

import logging
from typing import Dict, Any, List, Optional
from letta_client import AgentState

from src.agents.agent_factory import LettaAgentFactory
from src.tools.tool_registry import get_supervisor_tools

logger = logging.getLogger(__name__)


class Supervisor:
    """
    ATLAS Supervisor Agent using tool-based architecture with Letta runtime.

    The supervisor coordinates task execution by:
    - Planning and decomposing complex tasks into manageable sub-tasks
    - Managing todo items and tracking execution progress
    - Delegating specialized work to research, analysis, and writing agents
    - Maintaining session-scoped file operations for persistent outputs

    Uses Letta for persistent memory and tool execution, with all capabilities
    exposed through a unified tool interface for maximum flexibility.
    """

    def __init__(self, task_id: str):
        """
        Initialize the Supervisor agent with tools and Letta backend.

        Args:
            task_id: Unique identifier for the task being supervised

        Raises:
            RuntimeError: If Letta server is not available or tool registration fails
        """
        self.task_id = task_id
        self.factory = LettaAgentFactory()

        # Get supervisor tools from registry
        self.tools = get_supervisor_tools()

        # Create Letta agent with registered tools
        try:
            self.agent = self._create_agent_with_tools()
            logger.info(f"Supervisor agent created successfully: {self.agent.id}")
        except Exception as e:
            logger.error(f"Failed to create supervisor agent: {e}")
            raise RuntimeError(f"Could not initialize supervisor agent: {e}")

    def _create_agent_with_tools(self) -> AgentState:
        """
        Create Letta agent instance with supervisor tools registered.

        Creates the agent using the factory and registers all supervisor tools
        for task planning, todo management, file operations, and delegation.

        Returns:
            AgentState: The created Letta agent with tools registered

        Raises:
            Exception: If agent creation or tool registration fails
        """
        # Create base supervisor agent
        agent = self.factory.create_supervisor_agent(self.task_id)

        # Register tools with the agent
        for tool in self.tools:
            try:
                # Register each tool function with its metadata
                self.factory.client.agents.tools.add(
                    agent_id=agent.id,
                    function=tool["function"],
                    name=tool["name"],
                    description=tool["description"]
                )
                logger.debug(f"Registered tool: {tool['name']}")
            except Exception as e:
                logger.warning(f"Failed to register tool {tool['name']}: {e}")

        return agent

    def send_message(self, message: str) -> List[Dict[str, Any]]:
        """
        Send a message to the supervisor agent for processing.

        The agent will process the message using its available tools to:
        - Plan task execution and create sub-tasks
        - Update todo items and track progress
        - Save outputs and manage session files
        - Delegate work to specialized agents as needed

        Args:
            message: The user message or task instruction to process

        Returns:
            List of message responses from the agent, including tool execution results

        Raises:
            RuntimeError: If message sending fails or agent is unavailable
        """
        try:
            response = self.factory.send_message_to_agent(
                agent_id=self.agent.id,
                message=message
            )

            logger.info(f"Message sent to supervisor {self.agent.id}")
            return [{"content": msg.content, "role": msg.role} for msg in response]

        except Exception as e:
            logger.error(f"Failed to send message to supervisor: {e}")
            raise RuntimeError(f"Message processing failed: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status and state of the supervisor agent.

        Returns comprehensive status information including agent state,
        memory contents, and execution context for monitoring and debugging.

        Returns:
            Dictionary containing:
            - agent_id: The Letta agent identifier
            - task_id: The associated task identifier
            - memory_state: Current memory blocks and their contents
            - tools_available: List of registered tool names
            - last_activity: Timestamp of last message or tool execution

        Raises:
            RuntimeError: If status retrieval fails or agent is unavailable
        """
        try:
            # Get current agent state from Letta
            agent_state = self.factory.get_agent_state(self.agent.id)

            # Extract memory information
            memory_state = {}
            if hasattr(agent_state, 'memory') and agent_state.memory:
                for block in agent_state.memory.memory_blocks:
                    memory_state[block.label] = block.value

            # Compile status information
            status = {
                "agent_id": self.agent.id,
                "task_id": self.task_id,
                "memory_state": memory_state,
                "tools_available": [tool["name"] for tool in self.tools],
                "last_activity": getattr(agent_state, 'last_updated_at', None),
                "created_at": getattr(agent_state, 'created_at', None)
            }

            logger.debug(f"Retrieved status for supervisor {self.agent.id}")
            return status

        except Exception as e:
            logger.error(f"Failed to get supervisor status: {e}")
            raise RuntimeError(f"Status retrieval failed: {e}")

    def cleanup(self) -> None:
        """
        Clean up the supervisor agent and release resources.

        Deletes the Letta agent instance and performs cleanup operations.
        Should be called when the supervisor is no longer needed.

        Raises:
            RuntimeError: If cleanup operations fail
        """
        try:
            if hasattr(self, 'agent') and self.agent:
                self.factory.delete_agent(self.agent.id)
                logger.info(f"Supervisor agent {self.agent.id} cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to cleanup supervisor agent: {e}")
            raise RuntimeError(f"Cleanup failed: {e}")