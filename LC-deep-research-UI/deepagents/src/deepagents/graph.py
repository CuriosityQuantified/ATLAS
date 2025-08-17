from deepagents.sub_agent import _create_task_tool, SubAgent
from deepagents.model import get_default_model
from deepagents.tools import write_todos, write_file, read_file, ls, edit_file, respond_to_user, ask_user_question
from deepagents.state import DeepAgentState
from typing import Sequence, Union, Callable, Any, TypeVar, Type, Optional
from langchain_core.tools import BaseTool
from langchain_core.language_models import LanguageModelLike

from langgraph.prebuilt import create_react_agent

StateSchema = TypeVar("StateSchema", bound=DeepAgentState)
StateSchemaType = Type[StateSchema]

base_prompt = """You have access to a number of standard tools

## `ask_user_question`

Use this tool when you need clarification or additional information from the user. This will:
- Pause execution and wait for the user's response
- Show an input field in the UI for the user to respond
- Should be used SPARINGLY - only when truly needed for quality output
- NEVER use repeatedly for the same clarification - ask once and wait

Examples of good usage:
- "Which specific aspect of [topic] would you like me to focus on?"
- "Could you clarify what you mean by [ambiguous term]?"
- "Would you prefer a technical or general audience perspective?"

## `respond_to_user`

Use this tool ONLY for progress updates and status information, NOT for questions. Use this to:
- Provide progress updates during long-running operations
- Keep users informed about what you're currently doing
- Share findings as you discover them
- You can call this in PARALLEL with other tools

Examples of good usage:
- "Starting research on your topic..." [while calling internet_search]
- "Found relevant information, now analyzing..." [while processing data]
- "Compiling comprehensive report..." [while calling write_file]

IMPORTANT: Do NOT use respond_to_user to ask questions - use ask_user_question instead.

## `write_todos`

You have access to the `write_todos` tools to help you manage and plan tasks. Use these tools VERY frequently to ensure that you are tracking your tasks and giving the user visibility into your progress.
These tools are also EXTREMELY helpful for planning tasks, and for breaking down larger complex tasks into smaller steps. If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable.

It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed.
## `task`

- When doing web search, prefer to use the `task` tool in order to reduce context usage."""


def create_deep_agent(
    tools: Sequence[Union[BaseTool, Callable, dict[str, Any]]],
    instructions: str,
    model: Optional[Union[str, LanguageModelLike]] = None,
    subagents: list[SubAgent] = None,
    state_schema: Optional[StateSchemaType] = None,
):
    """Create a deep agent.

    This agent will by default have access to a tool to write todos (write_todos),
    and then four file editing tools: write_file, ls, read_file, edit_file.

    Args:
        tools: The additional tools the agent should have access to.
        instructions: The additional instructions the agent should have. Will go in
            the system prompt.
        model: The model to use.
        subagents: The subagents to use. Each subagent should be a dictionary with the
            following keys:
                - `name`
                - `description` (used by the main agent to decide whether to call the sub agent)
                - `prompt` (used as the system prompt in the subagent)
                - (optional) `tools`
        state_schema: The schema of the deep agent. Should subclass from DeepAgentState
    """
    prompt = instructions + base_prompt
    # Main agent gets both respond_to_user and ask_user_question
    built_in_tools = [write_todos, write_file, read_file, ls, edit_file, respond_to_user, ask_user_question]
    if model is None:
        model = get_default_model()
    state_schema = state_schema or DeepAgentState
    task_tool = _create_task_tool(
        list(tools) + built_in_tools,
        instructions,
        subagents or [],
        model,
        state_schema
    )
    all_tools = built_in_tools + list(tools) + [task_tool]
    return create_react_agent(
        model,
        prompt=prompt,
        tools=all_tools,
        state_schema=state_schema,
    )
