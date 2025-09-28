# Agent Factory for Letta-based ATLAS agents

import os
import logging
from typing import Optional, Dict, Any, List
from letta_client.client import Letta
from letta_client import (
    AgentState,
    LettaResponse  # Changed from MessageResponse
)
from letta.schemas.llm_config import LLMConfig
from letta.schemas.embedding_config import EmbeddingConfig

# Import local configuration
from .letta_config import (
    get_server_config,
    check_server_health,
    validate_environment,
    get_ade_connection_info
)

# Import OpenAI configuration instead of OpenRouter
from src.config.openai_config import OpenAIConfig

logger = logging.getLogger(__name__)

class LettaAgentFactory:
    """
    Factory for creating and managing Letta agents in the ATLAS hierarchy.

    Supports both local mode (with Web ADE) and cloud mode operation.
    In local mode, agents are visible and debuggable via https://app.letta.com
    """

    def __init__(self):
        """
        Initialize the Letta client with support for local or cloud mode.

        Local mode: Connects to server at http://localhost:8283
        Cloud mode: Uses API key for https://api.letta.com
        """
        # Get configuration from letta_config module
        config = get_server_config()

        # Initialize client based on mode
        if config["local_mode"]:
            # Local mode - no API key needed
            logger.info(f"Initializing Letta client in LOCAL mode at {config['base_url']}")

            # Check server health before connecting
            if not check_server_health():
                logger.warning(
                    "Letta server is not running. Start it with: letta server\n"
                    "Then connect Web ADE at https://app.letta.com to debug agents"
                )

            # Letta client from letta_client doesn't need api_key parameter
            self.client = Letta(
                base_url=config["base_url"]
            )

            # Log ADE connection instructions
            ade_info = get_ade_connection_info()
            logger.info("Web ADE available for debugging:")
            for instruction in ade_info["instructions"][:2]:
                logger.info(f"  {instruction}")

        else:
            # Cloud mode - use API key
            api_key = os.getenv("LETTA_API_KEY")
            if not api_key:
                raise ValueError(
                    "LETTA_API_KEY required for cloud mode. "
                    "Set LETTA_LOCAL_MODE=true for local operation."
                )

            logger.info("Initializing Letta client in CLOUD mode")
            # Note: letta_client doesn't support api_key parameter
            # Would need different authentication mechanism for cloud mode
            self.client = Letta(
                base_url=config.get("base_url", "https://api.letta.com")
            )

        self.local_mode = config["local_mode"]
        logger.info(f"Letta client initialized (Local mode: {self.local_mode})")

    def create_supervisor_agent(self, task_id: str) -> AgentState:
        """Create a Global Supervisor agent that coordinates sub-agents.

        The supervisor:
        - Owns the full task and decomposes it
        - Routes work to specialized team agents
        - Aggregates results and manages feedback loops
        """

        # Get OpenAI configuration for supervisor (uses GPT-4o)
        openai_llm = OpenAIConfig.get_llm_config(agent_type="supervisor")

        # Create LLM config for Letta
        llm_config = LLMConfig(
            model=openai_llm["model"],
            model_endpoint_type=openai_llm["model_endpoint_type"],
            model_endpoint=openai_llm["model_endpoint"],
            context_window=openai_llm["context_window"],
            model_wrapper=None,
            model_api_key=openai_llm.get("model_api_key")
        )

        # Create embedding config using OpenAI embeddings
        openai_embedding = OpenAIConfig.get_embedding_config()
        embedding_config = EmbeddingConfig(
            embedding_model=openai_embedding["embedding_model"],
            embedding_endpoint_type=openai_embedding["embedding_endpoint_type"],
            embedding_endpoint=openai_embedding["embedding_endpoint"],
            embedding_dim=openai_embedding["embedding_dim"],
            embedding_chunk_size=openai_embedding["embedding_chunk_size"],
            embedding_api_key=openai_embedding.get("embedding_api_key")
        )

        # Create supervisor agent with OpenAI model
        agent = self.client.agents.create(
            name=f"supervisor_{task_id}",
            description="Global Supervisor Agent for task coordination",
            system="""You are the Global Supervisor Agent for ATLAS.
            Your role is to:
            1. Decompose complex tasks into sub-tasks
            2. Delegate work to specialized agents (Research, Analysis, Writing)
            3. Coordinate agent responses and aggregate results
            4. Manage quality control and feedback loops

            You maintain the overall task context and ensure coherent output.""",
            llm_config=llm_config,
            embedding_config=embedding_config
        )

        logger.info(f"Created Supervisor agent: {agent.id} with model: {openai_llm['model']}")
        return agent

    def create_research_agent(self, task_id: str, context: str) -> AgentState:
        """Create a Research agent for information gathering.

        The research agent:
        - Gathers information from various sources
        - Aggregates and validates data
        - Provides sourced facts to other agents
        """

        # Get OpenAI configuration for research (uses GPT-4o-mini for cost efficiency)
        openai_llm = OpenAIConfig.get_llm_config(agent_type="research")

        # Create LLM config
        llm_config = LLMConfig(
            model=openai_llm["model"],
            model_endpoint_type=openai_llm["model_endpoint_type"],
            model_endpoint=openai_llm["model_endpoint"],
            context_window=openai_llm["context_window"],
            model_wrapper=None,
            model_api_key=openai_llm.get("model_api_key")
        )

        # Create embedding config using OpenAI embeddings
        openai_embedding = OpenAIConfig.get_embedding_config()
        embedding_config = EmbeddingConfig(
            embedding_model=openai_embedding["embedding_model"],
            embedding_endpoint_type=openai_embedding["embedding_endpoint_type"],
            embedding_endpoint=openai_embedding["embedding_endpoint"],
            embedding_dim=openai_embedding["embedding_dim"],
            embedding_chunk_size=openai_embedding["embedding_chunk_size"],
            embedding_api_key=openai_embedding.get("embedding_api_key")
        )

        agent = self.client.agents.create(
            name=f"research_{task_id}",
            description="Research Agent for information gathering",
            system=f"""You are a Research Agent specializing in information gathering.

            Context: {context}

            Your responsibilities:
            1. Find relevant information from multiple sources
            2. Validate and cross-reference facts
            3. Provide citations and sources
            4. Summarize findings clearly

            You focus on accuracy and comprehensiveness.""",
            llm_config=llm_config,
            embedding_config=embedding_config
        )

        logger.info(f"Created Research agent: {agent.id} with model: {openai_llm['model']}")
        return agent

    def create_analysis_agent(self, task_id: str, context: str) -> AgentState:
        """Create an Analysis agent for data interpretation.

        The analysis agent:
        - Interprets gathered information
        - Applies analytical frameworks (SWOT, pros/cons, etc.)
        - Generates insights and recommendations
        """

        # Get OpenAI configuration for analysis (uses GPT-4o-mini for cost efficiency)
        openai_llm = OpenAIConfig.get_llm_config(agent_type="analysis")

        # Create LLM config
        llm_config = LLMConfig(
            model=openai_llm["model"],
            model_endpoint_type=openai_llm["model_endpoint_type"],
            model_endpoint=openai_llm["model_endpoint"],
            context_window=openai_llm["context_window"],
            model_wrapper=None,
            model_api_key=openai_llm.get("model_api_key")
        )

        # Create embedding config using OpenAI embeddings
        openai_embedding = OpenAIConfig.get_embedding_config()
        embedding_config = EmbeddingConfig(
            embedding_model=openai_embedding["embedding_model"],
            embedding_endpoint_type=openai_embedding["embedding_endpoint_type"],
            embedding_endpoint=openai_embedding["embedding_endpoint"],
            embedding_dim=openai_embedding["embedding_dim"],
            embedding_chunk_size=openai_embedding["embedding_chunk_size"],
            embedding_api_key=openai_embedding.get("embedding_api_key")
        )

        agent = self.client.agents.create(
            name=f"analysis_{task_id}",
            description="Analysis Agent for data interpretation",
            system=f"""You are an Analysis Agent specializing in data interpretation.

            Context: {context}

            Your responsibilities:
            1. Analyze information from research agents
            2. Apply relevant analytical frameworks
            3. Identify patterns and insights
            4. Generate actionable recommendations

            You excel at structured thinking and clear analysis.""",
            llm_config=llm_config,
            embedding_config=embedding_config
        )

        logger.info(f"Created Analysis agent: {agent.id} with model: {openai_llm['model']}")
        return agent

    def create_writing_agent(self, task_id: str, context: str) -> AgentState:
        """Create a Writing agent for content generation.

        The writing agent:
        - Generates coherent written content
        - Maintains consistent tone and style
        - Structures information effectively
        """

        # Get OpenAI configuration for writing (uses GPT-4o for high-quality output)
        openai_llm = OpenAIConfig.get_llm_config(agent_type="writing")

        # Create LLM config
        llm_config = LLMConfig(
            model=openai_llm["model"],
            model_endpoint_type=openai_llm["model_endpoint_type"],
            model_endpoint=openai_llm["model_endpoint"],
            context_window=openai_llm["context_window"],
            model_wrapper=None,
            model_api_key=openai_llm.get("model_api_key")
        )

        # Create embedding config using OpenAI embeddings
        openai_embedding = OpenAIConfig.get_embedding_config()
        embedding_config = EmbeddingConfig(
            embedding_model=openai_embedding["embedding_model"],
            embedding_endpoint_type=openai_embedding["embedding_endpoint_type"],
            embedding_endpoint=openai_embedding["embedding_endpoint"],
            embedding_dim=openai_embedding["embedding_dim"],
            embedding_chunk_size=openai_embedding["embedding_chunk_size"],
            embedding_api_key=openai_embedding.get("embedding_api_key")
        )

        agent = self.client.agents.create(
            name=f"writing_{task_id}",
            description="Writing Agent for content generation",
            system=f"""You are a Writing Agent specializing in content creation.

            Context: {context}

            Your responsibilities:
            1. Transform analysis into clear written content
            2. Maintain consistent tone and style
            3. Structure information for maximum clarity
            4. Ensure coherence across all outputs

            You create professional, engaging content.""",
            llm_config=llm_config,
            embedding_config=embedding_config
        )

        logger.info(f"Created Writing agent: {agent.id} with model: {openai_llm['model']}")
        return agent

    def create_supervisor_agent_with_tools(self, tools: List[Dict]) -> AgentState:
        """Create supervisor agent with registered tools.

        The supervisor coordinates task decomposition, delegation, and result aggregation
        using available tools for planning, file operations, and sub-agent delegation.
        """

        agent = self.client.agents.create(
            name="supervisor_agent",
            description="Global Supervisor Agent with tool-based coordination",
            system="""You are the Global Supervisor Agent for ATLAS with comprehensive tool capabilities.

Your role and responsibilities:
1. **Task Decomposition**: Break complex tasks into manageable sub-tasks with clear dependencies
2. **Delegation**: Route work to specialized agents (research, analysis, writing) using delegation tools
3. **Coordination**: Manage parallel execution and dependency tracking across agents
4. **File Management**: Use file operations for session-scoped data storage and retrieval
5. **Quality Control**: Aggregate results, manage feedback loops, and ensure coherent outputs

Available tool categories:
- Planning tools: Decompose tasks and manage execution plans
- Todo management: Track task progress and dependencies
- File operations: Save outputs, load files, and manage session data
- Delegation tools: Send tasks to specialized sub-agents

Best practices:
- Always plan before executing - use planning tools to structure work
- Delegate based on agent expertise (research for data gathering, analysis for interpretation, writing for content)
- Use file tools to maintain session context and intermediate results
- Coordinate parallel work when no dependencies exist
- Aggregate and validate all sub-agent outputs before final delivery

You maintain the overall task context and ensure high-quality, coherent deliverables.""",
            tools=tools
        )

        logger.info(f"Created Supervisor agent with tools: {agent.id}")
        return agent

    def create_research_agent_with_tools(self, task_id: str, tools: List[Dict]) -> AgentState:
        """Create research agent with Firecrawl and file tools.

        Specialized in information gathering, source validation, and fact-checking
        using web search and file operations capabilities.
        """

        agent = self.client.agents.create(
            name=f"research_{task_id}",
            description="Research Agent with web search and file capabilities",
            system="""You are a Research Agent specializing in comprehensive information gathering.

Your core capabilities:
1. **Web Research**: Use Firecrawl tools to search the web, scrape content, and gather information
2. **Source Validation**: Cross-reference facts across multiple sources for accuracy
3. **Data Organization**: Structure findings logically with proper citations
4. **File Operations**: Save research outputs and load reference materials

Available tools:
- Firecrawl web search and scraping for current information
- File operations for saving research outputs and loading reference data
- Content extraction from various web sources

Research methodology:
- Start with broad searches to understand the topic landscape
- Narrow down to specific, authoritative sources
- Always provide citations and source URLs
- Cross-validate facts across multiple sources
- Organize findings by topic, relevance, and reliability
- Save comprehensive research outputs for other agents

Quality standards:
- Prioritize authoritative, recent sources
- Clearly distinguish between facts and opinions
- Highlight any conflicting information found
- Provide context for all findings
- Maintain objectivity and avoid bias

You excel at finding accurate, comprehensive information from diverse sources.""",
            tools=tools
        )

        logger.info(f"Created Research agent with tools: {agent.id}")
        return agent

    def create_analysis_agent_with_tools(self, task_id: str, tools: List[Dict]) -> AgentState:
        """Create analysis agent with E2B tools.

        Specialized in data interpretation, analytical frameworks, and code execution
        for comprehensive analysis and insights generation.
        """

        agent = self.client.agents.create(
            name=f"analysis_{task_id}",
            description="Analysis Agent with code execution and analytical capabilities",
            system="""You are an Analysis Agent specializing in data interpretation and analytical reasoning.

Your core capabilities:
1. **Data Analysis**: Interpret research data using statistical and analytical methods
2. **Code Execution**: Use E2B tools for computational analysis, data processing, and modeling
3. **Framework Application**: Apply analytical frameworks (SWOT, Porter's Five Forces, etc.)
4. **Insight Generation**: Transform raw data into actionable insights and recommendations

Available tools:
- E2B code execution for data processing, calculations, and analysis
- File operations for loading data and saving analytical outputs
- Computational capabilities for statistical analysis and modeling

Analytical approach:
- Begin with exploratory data analysis to understand patterns
- Apply appropriate analytical frameworks based on the context
- Use quantitative methods where data supports it
- Generate both descriptive and predictive insights
- Validate findings through multiple analytical lenses
- Present results with confidence levels and limitations

Types of analysis you excel at:
- Market analysis and competitive intelligence
- Financial modeling and risk assessment
- Trend analysis and forecasting
- SWOT analysis and strategic planning
- Data visualization and statistical analysis
- Scenario modeling and sensitivity analysis

Quality standards:
- Base conclusions on solid analytical foundations
- Clearly state assumptions and limitations
- Provide quantitative support where possible
- Distinguish between correlation and causation
- Present findings with appropriate uncertainty bounds

You transform raw information into strategic insights through rigorous analysis.""",
            tools=tools
        )

        logger.info(f"Created Analysis agent with tools: {agent.id}")
        return agent

    def create_writing_agent_with_tools(self, task_id: str, tools: List[Dict]) -> AgentState:
        """Create writing agent with document tools.

        Specialized in content creation, document structuring, and professional writing
        using comprehensive file operations and content management tools.
        """

        agent = self.client.agents.create(
            name=f"writing_{task_id}",
            description="Writing Agent with document creation and management capabilities",
            system="""You are a Writing Agent specializing in professional content creation and document management.

Your core capabilities:
1. **Content Creation**: Transform research and analysis into clear, engaging written content
2. **Document Structure**: Organize information with logical flow and professional formatting
3. **Style Management**: Maintain consistent tone, voice, and style throughout documents
4. **File Operations**: Manage document versions, load source materials, and save outputs

Available tools:
- File operations for document management, loading sources, and saving content
- Content structuring and formatting capabilities
- Document versioning and collaborative editing support

Writing expertise:
- Executive summaries and strategic briefings
- Technical documentation and reports
- Marketing content and communications
- Academic and research papers
- Business proposals and presentations
- Policy documents and analyses

Content development process:
- Analyze source materials from research and analysis agents
- Create comprehensive outlines with logical flow
- Develop content with appropriate depth and detail
- Ensure clarity, coherence, and professional presentation
- Adapt tone and style to intended audience
- Include proper citations and references

Quality standards:
- Clear, concise, and engaging prose
- Logical structure with smooth transitions
- Consistent formatting and style
- Error-free grammar and spelling
- Appropriate level of detail for the audience
- Professional presentation and layout

Content types you excel at:
- Strategic reports and executive briefings
- Market analysis documents and investment memos
- Research reports and white papers
- Product requirements and technical specifications
- Presentations and slide content
- Policy briefs and recommendation documents

You create compelling, professional content that effectively communicates complex information.""",
            tools=tools
        )

        logger.info(f"Created Writing agent with tools: {agent.id}")
        return agent

    def send_message_to_agent(self, agent_id: str, message: str) -> List:
        """Send a message to a specific agent and get the response."""
        from letta_client import MessageCreate

        response = self.client.agents.messages.create(
            agent_id=agent_id,
            messages=[
                MessageCreate(
                    role="user",
                    content=message
                )
            ]
        )
        return response.messages if hasattr(response, 'messages') else [response]

    def update_agent_memory(self, agent_id: str, memory_key: str, memory_value: str):
        """Update a specific memory block for an agent."""
        # Get current agent
        agent = self.client.agents.retrieve(agent_id)

        # Update memory using the new API
        # Note: This might need adjustment based on actual API
        self.client.agents.core_memory.update(
            agent_id=agent_id,
            label=memory_key,
            value=memory_value
        )
        logger.info(f"Updated memory for agent {agent_id}: {memory_key}")

    def get_agent_state(self, agent_id: str) -> AgentState:
        """Get the current state of an agent."""
        return self.client.agents.retrieve(agent_id)

    def delete_agent(self, agent_id: str):
        """Delete an agent when no longer needed."""
        self.client.agents.delete(agent_id)
        logger.info(f"Deleted agent: {agent_id}")

    def list_agents(self) -> List[AgentState]:
        """List all active agents."""
        return self.client.agents.list()

    def get_ade_debug_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get debugging information for viewing agent in Web ADE.

        Args:
            agent_id: The agent ID to debug

        Returns:
            dict: Information for debugging the agent in Web ADE
        """
        if not self.local_mode:
            return {
                "message": "Web ADE debugging only available in local mode",
                "local_mode": False
            }

        ade_info = get_ade_connection_info()
        return {
            "agent_id": agent_id,
            "server_url": ade_info["server_url"],
            "ade_url": ade_info["ade_url"],
            "instructions": [
                f"1. Open {ade_info['ade_url']}",
                "2. Go to Self-hosted tab",
                f"3. Connect to {ade_info['server_url']}",
                f"4. Select agent: {agent_id}",
                "5. Use Agent Simulator to interact and debug"
            ],
            "local_mode": True
        }