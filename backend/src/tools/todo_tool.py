"""
Todo Management Tool for ATLAS Agents
Minimal todo tracking with namespace isolation for multi-agent systems
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class TodoStatus(Enum):
    """Status states for todo items"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"

# Global storage with namespace isolation for multi-agent support
_todo_stores: Dict[str, List[Dict]] = {}

def create_todo(
    task_id: str,
    description: str,
    task_type: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    agent_namespace: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new todo item for tracking.

    Supports namespace isolation for multi-agent systems where each agent
    maintains its own todo list without conflicts.

    Args:
        task_id: Unique identifier for the task
        description: What needs to be done
        task_type: Which task type this is (research/analysis/writing)
        dependencies: List of task IDs that must complete first (required field)
        agent_namespace: Optional namespace for agent isolation (None = supervisor)

    Returns:
        The created todo item
    """

    # Determine namespace (default to supervisor)
    namespace = agent_namespace or "supervisor"
    if namespace not in _todo_stores:
        _todo_stores[namespace] = []
    todo = {
        "task_id": task_id,
        "description": description,
        "task_type": task_type,
        "status": TodoStatus.PENDING.value,
        "dependencies": dependencies or [],  # Always include dependencies field
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None
    }

    # Store in namespace-specific store
    _todo_stores[namespace].append(todo)

    return todo

def update_todo_status(
    task_id: str,
    status: str,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    agent_namespace: Optional[str] = None
) -> Dict[str, Any]:
    """
    Updates the status of a todo item.
    The supervisor maintains full context so no query functions are needed.

    Args:
        task_id: The task to update
        status: New status (pending/in_progress/completed/blocked/failed)
        result: Optional result data if completed
        error: Optional error message if failed
        agent_namespace: Optional namespace for agent isolation (None = supervisor)

    Returns:
        The updated todo item
    """
    # Determine namespace
    namespace = agent_namespace or "supervisor"
    if namespace not in _todo_stores:
        return {"error": f"No todos found in namespace '{namespace}'"}

    todos = _todo_stores[namespace]

    for todo in todos:
        if todo["task_id"] == task_id:
            todo["status"] = status
            todo["updated_at"] = datetime.now().isoformat()

            if status == TodoStatus.COMPLETED.value:
                todo["completed_at"] = datetime.now().isoformat()
                todo["result"] = result
            elif status == TodoStatus.FAILED.value:
                todo["error"] = error

            return todo

    return {"error": f"Todo with task_id '{task_id}' not found"}

# Utility functions for testing/debugging only (not exposed as tools)
def _get_all_todos(agent_namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """Internal function to retrieve all todos for debugging."""
    namespace = agent_namespace or "supervisor"
    return _todo_stores.get(namespace, [])

def _clear_todos(agent_namespace: Optional[str] = None) -> Dict[str, str]:
    """Internal function to clear todos for testing."""
    namespace = agent_namespace or "supervisor"
    if namespace in _todo_stores:
        _todo_stores[namespace] = []
        return {"status": f"All todos cleared for namespace '{namespace}'"}
    return {"status": f"No todos found in namespace '{namespace}'"}