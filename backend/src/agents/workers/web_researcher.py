"""
Module: web_researcher
Purpose: Web Research Worker agent using ReAct pattern with tools
Dependencies: WorkerAgent, web search tools
Used By: Research Team Supervisor
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from ..worker_agent import WorkerAgent
from ..base import AgentStatus
from ...agui.handlers import AGUIEventBroadcaster

logger = logging.getLogger(__name__)


# External Tool Functions
async def search_web(
    query: str,
    num_results: int = 10,
    search_type: str = "general"
) -> Dict[str, Any]:
    """
    Search the web using Tavily or similar search API.
    Returns structured search results.
    """
    logger.info(f"Searching web for: {query}")
    
    # TODO: Integrate actual Tavily API
    # For now, return simulated results
    import asyncio
    await asyncio.sleep(0.2)
    
    return {
        "query": query,
        "results": [
            {
                "title": f"Result 1 for {query}",
                "url": "https://example.com/result1",
                "snippet": "This is a relevant snippet containing information about the query...",
                "published_date": "2024-01-15"
            },
            {
                "title": f"Result 2 for {query}",
                "url": "https://example.org/result2",
                "snippet": "Another relevant result with different perspective on the topic...",
                "published_date": "2024-01-10"
            }
        ],
        "total_results": 25,
        "search_type": search_type
    }


async def extract_content(
    url: str,
    extract_type: str = "full"
) -> Dict[str, Any]:
    """
    Extract and parse content from a specific URL.
    Uses Firecrawl or similar service for content extraction.
    """
    logger.info(f"Extracting content from: {url}")
    
    # TODO: Integrate actual Firecrawl API
    import asyncio
    await asyncio.sleep(0.3)
    
    return {
        "url": url,
        "title": "Extracted Article Title",
        "content": "Full extracted content of the article...",
        "metadata": {
            "author": "John Doe",
            "published_date": "2024-01-15",
            "word_count": 1500,
            "reading_time": "6 minutes"
        },
        "extract_type": extract_type
    }


async def analyze_credibility(
    source: Dict[str, Any],
    check_author: bool = True,
    check_citations: bool = True
) -> Dict[str, Any]:
    """
    Analyze the credibility of a web source.
    Checks domain reputation, author credentials, citations, etc.
    """
    logger.info(f"Analyzing credibility of: {source.get('url', 'unknown')}")
    
    # TODO: Implement actual credibility checks
    import asyncio
    await asyncio.sleep(0.1)
    
    return {
        "url": source.get("url"),
        "credibility_score": 0.85,
        "factors": {
            "domain_reputation": 0.9,
            "author_credentials": 0.8 if check_author else None,
            "citation_quality": 0.85 if check_citations else None,
            "content_consistency": 0.9,
            "bias_indicators": ["minimal bias detected"]
        },
        "recommendation": "credible source"
    }


async def summarize_findings(
    content_list: List[Dict[str, Any]],
    summary_type: str = "comprehensive",
    max_length: int = 500
) -> Dict[str, Any]:
    """
    Summarize findings from multiple sources.
    Creates coherent summary with key points.
    """
    logger.info(f"Summarizing {len(content_list)} sources")
    
    # TODO: Use LLM for actual summarization
    import asyncio
    await asyncio.sleep(0.2)
    
    return {
        "summary": f"Comprehensive summary of {len(content_list)} sources: Key findings include...",
        "key_points": [
            "Key finding 1 from multiple sources",
            "Key finding 2 with consensus",
            "Key finding 3 with some disagreement"
        ],
        "source_consensus": {
            "high_agreement": ["Finding 1", "Finding 2"],
            "disputed": ["Finding 3"],
            "unique_insights": ["Source-specific insight"]
        },
        "summary_type": summary_type,
        "word_count": 450
    }


class WebResearchWorker(WorkerAgent):
    """
    Web Research Worker that uses ReAct pattern to gather information.
    
    Tools available:
    - search_web: Search for information
    - extract_content: Extract content from URLs
    - analyze_credibility: Check source credibility
    - summarize_findings: Summarize multiple sources
    """
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        agui_broadcaster: Optional[AGUIEventBroadcaster] = None,
        mlflow_tracker: Optional[Any] = None
    ):
        # Define external tools
        external_tools = [
            search_web,
            extract_content,
            analyze_credibility,
            summarize_findings
        ]
        
        super().__init__(
            agent_id="web_research_worker",
            agent_type="Web Research Worker",
            external_tools=external_tools,
            max_iterations=7,  # Allow more iterations for thorough research
            task_id=task_id,
            agui_broadcaster=agui_broadcaster,
            mlflow_tracker=mlflow_tracker
        )
        
        self.research_config = {
            "min_sources": 3,
            "credibility_threshold": 0.7,
            "search_strategies": ["broad", "specific", "academic"],
            "content_types": ["article", "research", "news", "blog"]
        }
        
        logger.info("Initialized Web Research Worker")
    
    async def execute_research(
        self,
        research_query: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        High-level research execution method.
        This is what gets called by the Research Supervisor's tool.
        """
        # Build context for research
        context = {
            "query": research_query,
            "requirements": requirements or {},
            "min_sources": requirements.get("min_sources", self.research_config["min_sources"]),
            "credibility_threshold": requirements.get("credibility_threshold", 
                                                    self.research_config["credibility_threshold"])
        }
        
        # Execute task using ReAct loop
        result = await self.execute_task(
            task_description=f"Research the following topic: {research_query}",
            context=context
        )
        
        return result
    
    async def _reason_about_task_tool(
        self,
        task_description: str,
        context: Dict[str, Any],
        history: List[Any]
    ) -> Dict[str, Any]:
        """
        Override reasoning tool with research-specific logic.
        """
        # Get sources found so far
        sources_found = context.get("sources_found", [])
        credible_sources = context.get("credible_sources", [])
        
        # Build reasoning context
        reasoning_context = f"""
Task: {task_description}
Context: {json.dumps(context, indent=2)}
Sources found: {len(sources_found)}
Credible sources: {len(credible_sources)}
Minimum required: {context.get('min_sources', 3)}

Previous steps:
{self._summarize_history(history)}

Available actions:
- search_web: Find new sources
- extract_content: Get full content from a URL
- analyze_credibility: Check if a source is credible
- summarize_findings: Create final summary
- return_findings: Complete the task

What should be the next step?
"""
        
        response = await self.send_to_letta(reasoning_context)
        content = response.get("content", "")
        
        # Update context based on history
        if history:
            for step in history:
                if step.action == "search_web" and step.observation:
                    # Add found sources to context
                    try:
                        results = json.loads(step.observation)
                        if "results" in results:
                            sources_found.extend(results["results"])
                    except:
                        pass
                elif step.action == "analyze_credibility" and step.observation:
                    # Track credible sources
                    try:
                        cred_result = json.loads(step.observation)
                        if cred_result.get("credibility_score", 0) >= context["credibility_threshold"]:
                            credible_sources.append(cred_result)
                    except:
                        pass
        
        context["sources_found"] = sources_found
        context["credible_sources"] = credible_sources
        
        # Determine next action based on research progress
        if len(credible_sources) >= context["min_sources"]:
            # We have enough credible sources
            if not any(step.action == "summarize_findings" for step in history):
                return {
                    "thought": f"I have found {len(credible_sources)} credible sources. Time to summarize the findings.",
                    "is_complete": False,
                    "next_action": "summarize_findings",
                    "action_args": {
                        "content_list": credible_sources,
                        "summary_type": "comprehensive"
                    }
                }
            else:
                return {
                    "thought": "Research is complete with summary prepared.",
                    "is_complete": True,
                    "next_action": "return_findings",
                    "confidence": 0.9
                }
        elif len(sources_found) > len(credible_sources):
            # We have unchecked sources
            unchecked = [s for s in sources_found if not self._is_source_checked(s, history)]
            if unchecked:
                return {
                    "thought": f"I have {len(unchecked)} sources to verify for credibility.",
                    "is_complete": False,
                    "next_action": "analyze_credibility",
                    "action_args": {
                        "source": unchecked[0],
                        "check_author": True,
                        "check_citations": True
                    }
                }
        
        # Need more sources
        return {
            "thought": f"I need to find more sources. Currently have {len(credible_sources)} credible sources.",
            "is_complete": False,
            "next_action": "search_web",
            "action_args": {
                "query": self._refine_search_query(context["query"], history),
                "num_results": 10,
                "search_type": "general"
            }
        }
    
    def _is_source_checked(self, source: Dict[str, Any], history: List[Any]) -> bool:
        """Check if a source has been analyzed for credibility"""
        source_url = source.get("url", "")
        for step in history:
            if step.action == "analyze_credibility" and source_url in str(step.action_input):
                return True
        return False
    
    def _refine_search_query(self, original_query: str, history: List[Any]) -> str:
        """Refine search query based on previous results"""
        # Count previous searches
        search_count = sum(1 for step in history if step.action == "search_web")
        
        # Apply different strategies
        if search_count == 0:
            return original_query
        elif search_count == 1:
            return f"{original_query} research academic"
        elif search_count == 2:
            return f"{original_query} latest news 2024"
        else:
            return f"{original_query} expert analysis"
    
    async def get_system_prompt(self) -> str:
        """Web research specific system prompt"""
        base_prompt = await super().get_system_prompt()
        
        return f"""{base_prompt}

WEB RESEARCH WORKER GUIDELINES:
- Prioritize credible and authoritative sources
- Verify information across multiple sources
- Extract key facts and insights
- Check publication dates for relevance
- Identify potential biases or conflicts

RESEARCH QUALITY CRITERIA:
- Minimum 3 credible sources required
- Credibility score threshold: 0.7
- Cross-reference critical claims
- Prefer primary sources
- Document all sources properly"""