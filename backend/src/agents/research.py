"""
Research Agent for ATLAS Multi-Agent System

The ResearchAgent uses Firecrawl tools for web search and information gathering,
processing delegation requests from the supervisor agent.
"""

import logging
from typing import Dict, Any, List, Optional
from letta_client import AgentState

from src.agents.agent_factory import LettaAgentFactory
from src.tools.tool_registry import get_research_tools

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Research Agent with Firecrawl and file tools.

    Specializes in information gathering from web sources and documents,
    fact validation, and structured research output generation.
    """

    def __init__(self, task_id: str):
        """
        Initialize the Research agent with tools and Letta backend.

        Args:
            task_id: Unique identifier for the research task

        Raises:
            RuntimeError: If Letta server is not available or tool registration fails
        """
        self.task_id = task_id
        self.factory = LettaAgentFactory()

        # Get research tools from registry
        self.tools = get_research_tools()

        # Create Letta agent with registered tools
        try:
            self.agent = self._create_agent_with_tools()
            logger.info(f"Research agent created successfully: {self.agent.id}")
        except Exception as e:
            logger.error(f"Failed to create research agent: {e}")
            raise RuntimeError(f"Could not initialize research agent: {e}")

    def _create_agent_with_tools(self) -> AgentState:
        """
        Create Letta agent instance with research tools registered.

        Returns:
            AgentState: The created Letta agent with tools registered

        Raises:
            Exception: If agent creation or tool registration fails
        """
        # Create research agent with factory method
        agent = self.factory.create_research_agent_with_tools(
            task_id=self.task_id,
            tools=self.tools
        )

        return agent

    def process_delegation(self, delegation_message: str) -> Dict[str, Any]:
        """
        Process a delegation request from the supervisor.

        The delegation message contains XML-structured context and task description
        that the research agent processes using its available tools.

        Args:
            delegation_message: XML-structured message with context, task, and restrictions

        Returns:
            Dictionary containing:
            - status: Success or failure indicator
            - results: Research findings and gathered information
            - sources: List of sources consulted
            - metadata: Execution metrics and details

        Raises:
            RuntimeError: If delegation processing fails
        """
        try:
            # Send delegation message to Letta agent
            response = self.factory.send_message_to_agent(
                agent_id=self.agent.id,
                message=delegation_message
            )

            # Process response from agent
            results = {
                "status": "success",
                "results": [],
                "sources": [],
                "metadata": {
                    "agent_id": self.agent.id,
                    "task_id": self.task_id,
                    "message_count": len(response)
                }
            }

            # Extract research findings from response
            for msg in response:
                if msg.get("role") == "assistant":
                    results["results"].append(msg.get("content", ""))

                # Extract any sources mentioned
                content = msg.get("content", "")
                if "http" in content:
                    # Simple extraction of URLs from content
                    import re
                    urls = re.findall(r'https?://[^\s<>"{}|\\^\[\]`]+', content)
                    results["sources"].extend(urls)

            # Remove duplicate sources
            results["sources"] = list(set(results["sources"]))

            logger.info(f"Research delegation processed successfully for task {self.task_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to process research delegation: {e}")
            raise RuntimeError(f"Research delegation failed: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status and state of the research agent.

        Returns:
            Dictionary containing:
            - agent_id: The Letta agent identifier
            - task_id: The associated task identifier
            - tools_available: List of registered tool names
            - memory_state: Current memory contents if available

        Raises:
            RuntimeError: If status retrieval fails
        """
        try:
            # Get current agent state from Letta
            agent_state = self.factory.get_agent_state(self.agent.id)

            # Compile status information
            status = {
                "agent_id": self.agent.id,
                "task_id": self.task_id,
                "tools_available": [tool["name"] for tool in self.tools],
                "created_at": getattr(agent_state, 'created_at', None),
                "last_activity": getattr(agent_state, 'last_updated_at', None)
            }

            # Extract memory if available
            if hasattr(agent_state, 'memory') and agent_state.memory:
                memory_state = {}
                for block in agent_state.memory.memory_blocks:
                    memory_state[block.label] = block.value
                status["memory_state"] = memory_state

            logger.debug(f"Retrieved status for research agent {self.agent.id}")
            return status

        except Exception as e:
            logger.error(f"Failed to get research agent status: {e}")
            raise RuntimeError(f"Status retrieval failed: {e}")

    def cleanup(self) -> None:
        """
        Clean up the research agent and release resources.

        Deletes the Letta agent instance and performs cleanup operations.
        Should be called when the agent is no longer needed.

        Raises:
            RuntimeError: If cleanup operations fail
        """
        try:
            if hasattr(self, 'agent') and self.agent:
                self.factory.delete_agent(self.agent.id)
                logger.info(f"Research agent {self.agent.id} cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to cleanup research agent: {e}")
            raise RuntimeError(f"Cleanup failed: {e}")