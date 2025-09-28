"""
Planning Tool for ATLAS Agents
Decomposes complex tasks into manageable sub-tasks using LLM reasoning
Supports namespace isolation for multi-agent systems
"""

from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

# Global storage with namespace isolation for multi-agent support
_plan_stores: Dict[str, List[Dict]] = {}

def plan_task(task_description: str, context: str = "", agent_memory: Optional[str] = None,
              agent_namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Decomposes a complex task into a structured plan with sub-tasks.

    Supports namespace isolation for multi-agent systems where each agent
    maintains its own planning context without conflicts.

    Args:
        task_description: The main task to be accomplished
        context: Additional context or constraints for planning
        agent_memory: Optional memory/history from the agent to inform planning
        agent_namespace: Optional namespace for agent isolation (None = supervisor)

    Returns:
        A dictionary containing:
        - plan_id: Unique identifier for this plan
        - main_goal: The primary objective
        - sub_tasks: List of decomposed tasks with priorities
        - dependencies: Task dependencies and sequencing
        - estimated_duration: Rough time estimate
    """

    # Determine namespace (default to supervisor)
    namespace = agent_namespace or "supervisor"
    if namespace not in _plan_stores:
        _plan_stores[namespace] = []

    # Try to use LLM for intelligent planning
    try:
        # Import call_model utility if available
        from src.utils.call_model import call_model

        # Construct planning prompt
        planning_prompt = f"""
        You are a task planning assistant. Decompose the following task into actionable sub-tasks.

        Main Task: {task_description}

        Context: {context if context else 'No additional context provided'}

        Agent Memory: {agent_memory if agent_memory else 'No prior memory'}

        Please create a structured plan with:
        1. 3-5 specific sub-tasks
        2. Clear dependencies between tasks (required for each task)
        3. Assignment to appropriate task types (research/analysis/writing)

        Respond in JSON format:
        {{
            "sub_tasks": [
                {{
                    "id": "task_1",
                    "description": "specific task description",
                    "task_type": "research|analysis|writing",
                    "dependencies": []
                }}
            ],
            "estimated_duration": "time estimate",
            "reasoning": "brief explanation of the plan"
        }}
        """

        # Call LLM for planning
        response = call_model(
            messages=[{"role": "user", "content": planning_prompt}],
            model="gpt-4o-mini",  # Use efficient model for planning
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        # Parse LLM response
        llm_plan = json.loads(response)

        # Structure the plan
        plan = {
            "plan_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "main_goal": task_description,
            "context": context,
            "sub_tasks": llm_plan.get("sub_tasks", []),
            "estimated_duration": llm_plan.get("estimated_duration", "30-60 minutes"),
            "reasoning": llm_plan.get("reasoning", ""),
            "created_at": datetime.now().isoformat(),
            "llm_generated": True
        }

        # Add status field to each sub-task
        for task in plan["sub_tasks"]:
            task["status"] = "pending"

        # Store plan in namespace-specific store
        _plan_stores[namespace].append(plan)

        return plan

    except (ImportError, Exception) as e:
        # Fallback to template-based planning if LLM fails or call_model not available
        print(f"LLM planning failed, using template: {e}")

        plan = {
            "plan_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "main_goal": task_description,
            "context": context,
            "sub_tasks": [
                {
                    "id": "task_1",
                    "description": f"Research information about: {task_description}",
                    "task_type": "research",
                    "dependencies": [],
                    "status": "pending"
                },
                {
                    "id": "task_2",
                    "description": f"Analyze findings for: {task_description}",
                    "task_type": "analysis",
                    "dependencies": ["task_1"],
                    "status": "pending"
                },
                {
                    "id": "task_3",
                    "description": f"Create report about: {task_description}",
                    "task_type": "writing",
                    "dependencies": ["task_2"],
                    "status": "pending"
                }
            ],
            "estimated_duration": "30-60 minutes",
            "created_at": datetime.now().isoformat()
        }

        # Store plan in namespace-specific store
        _plan_stores[namespace].append(plan)

        return plan

def update_plan(plan_id: str, updates: Dict[str, Any], feedback: str = "",
                agent_namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Updates an existing plan based on execution feedback.

    Args:
        plan_id: The plan identifier to update
        updates: Dictionary of updates to apply
        feedback: Execution feedback to inform plan adjustments
        agent_namespace: Optional namespace for agent isolation (None = supervisor)

    Returns:
        Updated plan dictionary
    """

    # Determine namespace
    namespace = agent_namespace or "supervisor"
    try:
        from src.utils.call_model import call_model

        # Construct update prompt
        update_prompt = f"""
        You need to update an existing task plan based on execution feedback.

        Plan ID: {plan_id}
        Current Updates: {json.dumps(updates, indent=2)}
        Feedback: {feedback if feedback else 'No specific feedback'}

        Based on this information, suggest plan adjustments:
        1. Should any tasks be modified?
        2. Should task priorities change?
        3. Are new tasks needed?
        4. Should any tasks be removed?

        Respond in JSON format:
        {{
            "modifications": [
                {{
                    "task_id": "id",
                    "change_type": "modify|add|remove",
                    "details": "description of change"
                }}
            ],
            "reasoning": "explanation for the changes"
        }}
        """

        # Call LLM for plan updates
        response = call_model(
            messages=[{"role": "user", "content": update_prompt}],
            model="gpt-4o-mini",
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        llm_updates = json.loads(response)

        return {
            "plan_id": plan_id,
            "status": "updated",
            "updates_applied": updates,
            "llm_suggestions": llm_updates.get("modifications", []),
            "reasoning": llm_updates.get("reasoning", ""),
            "updated_at": datetime.now().isoformat(),
            "llm_assisted": True
        }

    except Exception as e:
        # Fallback to simple update if LLM fails
        print(f"LLM update failed, using simple update: {e}")
        return {
            "plan_id": plan_id,
            "status": "updated",
            "updates_applied": updates,
            "updated_at": datetime.now().isoformat(),
            "llm_assisted": False
        }

def evaluate_plan_progress(plan_id: str) -> Dict[str, Any]:
    """
    Evaluates the current progress of a plan.

    Args:
        plan_id: The plan identifier to evaluate

    Returns:
        Progress report with completion percentage and bottlenecks
    """
    # Placeholder for progress evaluation
    return {
        "plan_id": plan_id,
        "overall_progress": 0.0,
        "completed_tasks": [],
        "in_progress_tasks": [],
        "blocked_tasks": [],
        "estimated_completion": "unknown"
    }