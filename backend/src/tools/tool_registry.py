"""
Tool Registry for ATLAS Agents
Defines and registers tools that Letta agents can use
"""

from typing import List, Dict, Any, Callable
from src.tools import planning_tool, todo_tool, file_tool
from src.tools import research_tool, analysis_tool, writing_tool

def get_supervisor_tools() -> List[Dict[str, Any]]:
    """
    Returns the list of tools available to the supervisor agent.

    Each tool definition includes:
    - The callable function
    - A clear description for the LLM to understand when to use it
    - Parameter documentation

    Returns:
        List of tool definitions for Letta agent registration
    """

    tools = [
        # Planning Tools
        {
            "function": planning_tool.plan_task,
            "name": "plan_task",
            "description": "Create a structured execution plan for a complex task. Use this when you need to break down a large task into smaller, manageable sub-tasks.",
        },
        {
            "function": planning_tool.update_plan,
            "name": "update_plan",
            "description": "Update an existing plan based on execution feedback or changing requirements. Use when tasks are completed or when adjustments are needed.",
        },

        # Todo Management Tools
        {
            "function": todo_tool.create_todo,
            "name": "create_todo",
            "description": "Create a new todo item to track a specific task. Use when adding tasks from the plan to the execution queue.",
        },
        {
            "function": todo_tool.update_todo_status,
            "name": "update_todo",
            "description": "Update the status of a todo item (pending/in_progress/completed/failed). Use to track task execution progress.",
        },

        # File Operations Tools (Session-scoped)
        {
            "function": file_tool.save_output,
            "name": "save_output",
            "description": "Save content to a file in the session directory. Use to persist research findings, analysis results, or final reports.",
        },
        {
            "function": file_tool.load_file,
            "name": "load_file",
            "description": "Read content from a file in the session directory. Use to retrieve previous work or reference materials.",
        },
        {
            "function": file_tool.append_content,
            "name": "append_content",
            "description": "Add content to an existing file in the session directory. Use for incremental updates to reports or logs.",
        },
        {
            "function": file_tool.list_outputs,
            "name": "list_outputs",
            "description": "List all files in the session directory. Use to see what outputs have been generated.",
        },

        # Delegation Tools
        {
            "function": research_tool.delegate_research,
            "name": "delegate_research",
            "description": "Delegate research tasks to research agent. Provide context, task description, and restrictions.",
        },
        {
            "function": analysis_tool.delegate_analysis,
            "name": "delegate_analysis",
            "description": "Delegate analysis tasks to analysis agent. Provide context, task description, and restrictions.",
        },
        {
            "function": writing_tool.delegate_writing,
            "name": "delegate_writing",
            "description": "Delegate writing tasks to writing agent. Provide context, task description, and restrictions.",
        },
    ]

    return tools


def get_research_tools() -> List[Dict[str, Any]]:
    """
    Returns the list of tools available to the research agent.

    Research agents get:
    - Firecrawl tools for web search and scraping (to be implemented)
    - File operations for saving research outputs
    - Namespaced planning/todo tools for sub-task management

    Returns:
        List of tool definitions for research agent
    """
    tools = [
        # Planning Tools (namespaced for research agent)
        {
            "function": planning_tool.plan_task,
            "name": "plan_research",
            "description": "Create a research plan for gathering information. Break down research into specific sources and topics.",
        },
        {
            "function": planning_tool.update_plan,
            "name": "update_research_plan",
            "description": "Update research plan based on findings and new directions discovered during research.",
        },

        # Todo Management (namespaced for research agent)
        {
            "function": todo_tool.create_todo,
            "name": "create_research_todo",
            "description": "Create a research task to track specific information gathering activities.",
        },
        {
            "function": todo_tool.update_todo_status,
            "name": "update_research_todo",
            "description": "Update the status of a research task as information is gathered.",
        },

        # File Operations for research outputs
        {
            "function": file_tool.save_output,
            "name": "save_research",
            "description": "Save research findings to a file for later use by other agents.",
        },
        {
            "function": file_tool.load_file,
            "name": "load_reference",
            "description": "Load reference materials or previous research outputs.",
        },
        {
            "function": file_tool.list_outputs,
            "name": "list_research_files",
            "description": "List available research files in the session directory.",
        },

        # TODO: Add Firecrawl tools when available
        # - web_search: Search the web for information
        # - scrape_url: Extract content from specific URLs
        # - crawl_site: Systematically crawl a website
    ]

    return tools


def get_analysis_tools() -> List[Dict[str, Any]]:
    """
    Returns the list of tools available to the analysis agent.

    Analysis agents get:
    - E2B tools for code execution and data processing (to be implemented)
    - File operations for loading data and saving analysis
    - Namespaced planning/todo tools for analysis task management

    Returns:
        List of tool definitions for analysis agent
    """
    tools = [
        # Planning Tools (namespaced for analysis agent)
        {
            "function": planning_tool.plan_task,
            "name": "plan_analysis",
            "description": "Create an analysis plan with specific analytical frameworks and methodologies.",
        },
        {
            "function": planning_tool.update_plan,
            "name": "update_analysis_plan",
            "description": "Update analysis plan based on initial findings and insights.",
        },

        # Todo Management (namespaced for analysis agent)
        {
            "function": todo_tool.create_todo,
            "name": "create_analysis_todo",
            "description": "Create an analysis task for specific data interpretation or framework application.",
        },
        {
            "function": todo_tool.update_todo_status,
            "name": "update_analysis_todo",
            "description": "Update the status of analysis tasks as insights are generated.",
        },

        # File Operations for analysis work
        {
            "function": file_tool.save_output,
            "name": "save_analysis",
            "description": "Save analysis results, insights, and recommendations to a file.",
        },
        {
            "function": file_tool.load_file,
            "name": "load_data",
            "description": "Load research data or previous analysis for further processing.",
        },
        {
            "function": file_tool.append_content,
            "name": "append_analysis",
            "description": "Add incremental analysis results to an existing report.",
        },

        # TODO: Add E2B tools when available
        # - execute_code: Run Python code for data analysis
        # - create_visualization: Generate charts and graphs
        # - statistical_analysis: Perform statistical calculations
    ]

    return tools


def get_writing_tools() -> List[Dict[str, Any]]:
    """
    Returns the list of tools available to the writing agent.

    Writing agents get:
    - Document creation and formatting tools
    - File operations for content management
    - Namespaced planning/todo tools for writing task tracking

    Returns:
        List of tool definitions for writing agent
    """
    tools = [
        # Planning Tools (namespaced for writing agent)
        {
            "function": planning_tool.plan_task,
            "name": "plan_document",
            "description": "Create a document structure plan with sections, tone, and key messages.",
        },
        {
            "function": planning_tool.update_plan,
            "name": "update_document_plan",
            "description": "Update document plan based on content requirements and feedback.",
        },

        # Todo Management (namespaced for writing agent)
        {
            "function": todo_tool.create_todo,
            "name": "create_writing_todo",
            "description": "Create a writing task for specific sections or content pieces.",
        },
        {
            "function": todo_tool.update_todo_status,
            "name": "update_writing_todo",
            "description": "Update the status of writing tasks as sections are completed.",
        },

        # File Operations for document management
        {
            "function": file_tool.save_output,
            "name": "save_document",
            "description": "Save written content as a complete document or report.",
        },
        {
            "function": file_tool.load_file,
            "name": "load_content",
            "description": "Load research and analysis outputs to incorporate into writing.",
        },
        {
            "function": file_tool.append_content,
            "name": "append_section",
            "description": "Add new sections or paragraphs to an existing document.",
        },
        {
            "function": file_tool.list_outputs,
            "name": "list_documents",
            "description": "List all documents and content files in the session.",
        },
    ]

    return tools