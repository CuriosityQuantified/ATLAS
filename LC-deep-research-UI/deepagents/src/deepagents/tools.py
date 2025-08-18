from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command, interrupt
from langchain_core.messages import ToolMessage
from typing import Annotated
from langgraph.prebuilt import InjectedState
from datetime import datetime
import os

from deepagents.prompts import (
    WRITE_TODOS_DESCRIPTION,
    EDIT_DESCRIPTION,
    TOOL_DESCRIPTION,
)
from deepagents.state import Todo, DeepAgentState
from typing import Optional


@tool(description=WRITE_TODOS_DESCRIPTION)
def write_todos(
    todos: list[Todo], 
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[DeepAgentState, InjectedState]
) -> Command:
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(f"Updated todo list to {todos}", tool_call_id=tool_call_id)
            ],
            # Reset consecutive respond_to_user counter since we're using a different tool
            "consecutive_respond_calls": 0,
            "last_tool_used": "write_todos"
        }
    )


def ls(state: Annotated[DeepAgentState, InjectedState]) -> list[str]:
    """List all files"""
    return list(state.get("files", {}).keys())


@tool(description=TOOL_DESCRIPTION)
def read_file(
    file_path: str,
    state: Annotated[DeepAgentState, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """Read file."""
    mock_filesystem = state.get("files", {})
    if file_path not in mock_filesystem:
        return f"Error: File '{file_path}' not found"

    # Get file content
    content = mock_filesystem[file_path]

    # Handle empty file
    if not content or content.strip() == "":
        return "System reminder: File exists but has empty contents"

    # Split content into lines
    lines = content.splitlines()

    # Apply line offset and limit
    start_idx = offset
    end_idx = min(start_idx + limit, len(lines))

    # Handle case where offset is beyond file length
    if start_idx >= len(lines):
        return f"Error: Line offset {offset} exceeds file length ({len(lines)} lines)"

    # Format output with line numbers (cat -n format)
    result_lines = []
    for i in range(start_idx, end_idx):
        line_content = lines[i]

        # Truncate lines longer than 2000 characters
        if len(line_content) > 2000:
            line_content = line_content[:2000]

        # Line numbers start at 1, so add 1 to the index
        line_number = i + 1
        result_lines.append(f"{line_number:6d}\t{line_content}")

    return "\n".join(result_lines)


def write_file(
    file_path: str,
    content: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Write to a file."""
    files = state.get("files", {})
    files[file_path] = content
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(f"Updated file {file_path}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description=EDIT_DESCRIPTION)
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    replace_all: bool = False,
) -> str:
    """Write to a file."""
    mock_filesystem = state.get("files", {})
    # Check if file exists in mock filesystem
    if file_path not in mock_filesystem:
        return f"Error: File '{file_path}' not found"

    # Get current file content
    content = mock_filesystem[file_path]

    # Check if old_string exists in the file
    if old_string not in content:
        return f"Error: String not found in file: '{old_string}'"

    # If not replace_all, check for uniqueness
    if not replace_all:
        occurrences = content.count(old_string)
        if occurrences > 1:
            return f"Error: String '{old_string}' appears {occurrences} times in file. Use replace_all=True to replace all instances, or provide a more specific string with surrounding context."
        elif occurrences == 0:
            return f"Error: String not found in file: '{old_string}'"

    # Perform the replacement
    if replace_all:
        new_content = content.replace(old_string, new_string)
        replacement_count = content.count(old_string)
        result_msg = f"Successfully replaced {replacement_count} instance(s) of the string in '{file_path}'"
    else:
        new_content = content.replace(
            old_string, new_string, 1
        )  # Replace only first occurrence
        result_msg = f"Successfully replaced string in '{file_path}'"

    # Update the mock filesystem
    mock_filesystem[file_path] = new_content
    return Command(
        update={
            "files": mock_filesystem,
            "messages": [
                ToolMessage(f"Updated file {file_path}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description="Send a real-time response to the user while continuing other work. Use this ONLY for progress updates and status information, NOT for questions. If you need user input, use ask_user_question instead.")
def respond_to_user(
    message: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[DeepAgentState, InjectedState],
    status: Optional[str] = None
) -> Command:
    """
    Send an immediate response to the user while continuing other operations.
    
    Args:
        message: The message to send to the user
        status: Optional status indicator ("thinking", "researching", "analyzing", "writing", "completed")
    
    This tool allows agents to:
    - Provide real-time progress updates
    - Keep users informed during long operations
    - Send parallel communications while executing other tools
    - Reduce perceived latency and improve user experience
    """
    # Get current usage tracking from state
    consecutive_calls = state.get("consecutive_respond_calls", 0)
    last_tool = state.get("last_tool_used", "")
    
    # HARD LIMIT ENFORCEMENT: Block if already called 2 times consecutively
    if last_tool == "respond_to_user" and consecutive_calls >= 2:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        "ERROR: respond_to_user limit exceeded (max 2 consecutive calls). "
                        "Use other tools before calling respond_to_user again.",
                        tool_call_id=tool_call_id
                    )
                ],
                # Reset the counter since we're blocking
                "consecutive_respond_calls": 0,
                "last_tool_used": "respond_to_user_blocked"
            }
        )
    
    # Update usage tracking
    new_consecutive = consecutive_calls + 1 if last_tool == "respond_to_user" else 1
    tool_usage = state.get("tool_usage", {})
    tool_usage["respond_to_user"] = tool_usage.get("respond_to_user", 0) + 1
    
    # Create a structured response for the frontend
    response_content = {
        "type": "user_response",
        "message": message,
        "status": status,
        "timestamp": "now"  # Frontend can handle timestamp formatting
    }
    
    # Format the tool message without "User Response:" prefix
    tool_message = message
    if status:
        tool_message += f" [Status: {status}]"
    
    return Command(
        update={
            "messages": [
                ToolMessage(tool_message, tool_call_id=tool_call_id, additional_kwargs=response_content)
            ],
            "tool_usage": tool_usage,
            "consecutive_respond_calls": new_consecutive,
            "last_tool_used": "respond_to_user"
        }
    )


# Feature flag to control interrupt vs command implementation
USE_INTERRUPT_PATTERN = os.getenv("USE_INTERRUPT_PATTERN", "false").lower() == "true"

if USE_INTERRUPT_PATTERN:
    @tool(description="Ask the user a clarifying question and wait for their response. Use this when you need additional information to provide better results. The execution will pause until the user responds.")
    def ask_user_question(
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        Ask the user a question using LangGraph's interrupt pattern.
        This will pause execution until the user responds.
        
        Args:
            question: The question to ask the user
            context: Optional context about why you're asking this question
        
        This tool:
        - Pauses execution until user responds via interrupt
        - Shows an input field in the UI for the user to type their answer
        - Should be used sparingly and only when truly needed
        - Should NOT be used repeatedly for the same clarification
        """
        # Create interrupt data structure
        interrupt_data = {
            "type": "user_question",
            "question": question,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        # Use interrupt to pause execution
        # The graph will pause here and wait for Command(resume=answer)
        user_response = interrupt(interrupt_data)
        
        # Return the user's actual response
        return f"User answered: {user_response}"
else:
    # Original implementation for backward compatibility
    @tool(description="Ask the user a clarifying question and wait for their response. Use this when you need additional information to provide better results. The execution will pause until the user responds.")
    def ask_user_question(
        question: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[DeepAgentState, InjectedState],
        context: Optional[str] = None
    ) -> Command:
        """
        Ask the user a question and wait for their response.
        
        Args:
            question: The question to ask the user
            context: Optional context about why you're asking this question
        
        This tool:
        - Pauses execution until user responds
        - Shows an input field in the UI for the user to type their answer
        - Should be used sparingly and only when truly needed
        - Should NOT be used repeatedly for the same clarification
        """
        # Create a structured response that signals the frontend to show an input field
        question_content = {
            "type": "user_question",
            "question": question,
            "context": context,
            "needs_response": True,
            "timestamp": "now"
        }
        
        # Format the tool message
        tool_message = f"Question: {question}"
        if context:
            tool_message += f" (Context: {context})"
        
        return Command(
            update={
                "messages": [
                    ToolMessage(tool_message, tool_call_id=tool_call_id, additional_kwargs=question_content)
                ],
                # Reset consecutive respond_to_user counter since we're using a different tool
                "consecutive_respond_calls": 0,
                "last_tool_used": "ask_user_question"
            }
        )
