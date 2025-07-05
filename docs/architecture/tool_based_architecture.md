# ATLAS Tool-Based Architecture

## Overview

The ATLAS system implements a strict tool-based architecture where ALL agent actions are tool calls, enabling parallel execution, clear communication patterns, and comprehensive tracking.

## Key Architectural Components

### 1. Base Classes

#### SupervisorAgent (`supervisor_agent.py`)
- Base class for all supervisor agents
- Supports multiple parallel tool calls via LangGraph
- Manages state across iterations
- Implements conditional routing for tool execution

Key features:
- `execute_with_tools()` - Main entry point for task execution
- Automatic tool parameter extraction
- Parallel execution tracking
- State-based workflow management

#### WorkerAgent (`worker_agent.py`)
- Base class for all worker agents
- Implements ReAct (Reasoning-Action) pattern
- ALL operations are tools (including reasoning)
- Returns structured results to supervisors

Key features:
- `reason_about_task` - Reasoning as a tool
- `return_findings` - Structured result tool
- Configurable max iterations
- Tool-based execution loop

### 2. Agent Hierarchy

```
Global Supervisor V2
├── respond_to_user() [User Communication Tool]
├── call_research_team() → Research Team Supervisor
│   ├── call_web_researcher() → Web Research Worker
│   ├── call_document_analyst() → Document Analyst Worker
│   ├── call_academic_researcher() → Academic Research Worker
│   └── call_source_verifier() → Source Verification Worker
├── call_analysis_team() → Analysis Team Supervisor
│   └── [Workers...]
├── call_writing_team() → Writing Team Supervisor
│   └── [Workers...]
└── call_rating_team() → Rating Team Supervisor
    └── [Workers...]
```

### 3. Tool Communication Pattern

#### Supervisor → Team Tool Call
```python
async def call_research_team(
    task_description: str,
    priority: str = "medium",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Tool function that instantiates and runs Research Team Supervisor"""
    supervisor = ResearchTeamSupervisor(...)
    result = await supervisor.execute_with_tools(...)
    return {
        "tool_name": "research_team",
        "status": "complete",
        "findings": result["content"],
        "metadata": {...}
    }
```

#### Worker ReAct Loop
```python
# Step 1: Reason (as a tool)
reasoning_result = await reason_about_task(task, context, history)

# Step 2: Act (execute chosen tool)
if reasoning_result["next_action"] == "search_web":
    tool_result = await search_web(**reasoning_result["action_args"])

# Step 3: Observe and iterate
history.append(ReActStep(thought=..., action=..., observation=...))
```

### 4. Parallel Execution

Supervisors can make multiple tool calls in parallel:

```python
# Global Supervisor can call multiple teams at once
tool_calls = [
    {"name": "call_research_team", "args": {...}},
    {"name": "call_analysis_team", "args": {...}}
]

# LangGraph's ToolNode executes them in parallel
results = await tool_node.execute(tool_calls)
```

### 5. User Communication

The Global Supervisor V2 includes a `respond_to_user` tool for continuous updates:

```python
await respond_to_user(
    message="Progress update: Research team has found 5 relevant sources",
    message_type="update",
    include_status=True,
    request_input=False
)
```

## Implementation Status

### ✅ Completed
- Base supervisor class with parallel tool support
- Base worker class with ReAct pattern
- Global Supervisor V2 with user communication
- Research Team Supervisor example
- Web Research Worker example
- Tool function patterns

### 🔄 In Progress
- LangGraph workflow integration
- Full team supervisor implementations
- All worker agent implementations

### 📋 TODO
- Analysis Team Supervisor and workers
- Writing Team Supervisor and workers
- Rating Team Supervisor and workers
- Integration with existing AG-UI system
- MLflow tracking for tool calls

## Key Benefits

1. **Parallelism**: Supervisors can call multiple tools simultaneously
2. **Clarity**: Every action is a tool call with clear inputs/outputs
3. **Tracking**: All tool calls can be tracked and monitored
4. **Flexibility**: Easy to add new tools or modify existing ones
5. **Human-in-the-Loop**: User communication integrated as a tool

## Testing

Run the test suite to validate the architecture:

```bash
cd backend
python test_tool_architecture.py
```

This tests:
- Worker ReAct loops
- Supervisor parallel execution
- User communication
- Tool result propagation

## Next Steps

1. Complete LangGraph integration for production use
2. Implement remaining team supervisors
3. Create all worker agents
4. Integrate with frontend via AG-UI
5. Add comprehensive MLflow tracking
6. Performance optimization for parallel execution