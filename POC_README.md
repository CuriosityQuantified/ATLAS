# ATLAS POC - Streamlined Multi-Agent System

## Overview
This is the streamlined Proof of Concept (POC) for ATLAS - a hierarchical multi-agent system using:
- **Letta** - Agent framework with persistent memory (running locally on port 8283)
- **CopilotKit** - React-based AI interface
- **AG-UI** - Real-time WebSocket/SSE middleware
- **MLflow** - LLM observability and tracking
- **PostgreSQL** - Data persistence

## Phase 2 Architecture (Current Implementation)

### Tool-Based Supervisor Design
The supervisor agent uses a streamlined set of tools for task orchestration:

**Planning Tools** (`planning_tool.py`):
- `plan_task()`: LLM-based decomposition with task_type and dependencies
- `update_plan()`: Modifies plans based on execution feedback
- Namespace isolation for multi-agent support

**Todo Management** (`todo_tool.py`):
- `create_todo()`: Adds tasks with explicit dependencies
- `update_todo_status()`: Updates task progress
- No query tools - supervisor maintains full context

**File Operations** (`file_tool.py`):
- `save_output()`: Writes to session directory
- `load_file()`: Reads from session directory
- `append_content()`: Incremental content updates
- `list_outputs()`: Lists session files

**Delegation Tools** (XML-structured prompts):
- `delegate_research()`: Sends tasks to research agent
- `delegate_analysis()`: Sends tasks to analysis agent
- `delegate_writing()`: Sends tasks to writing agent
- Each delegation includes context, task_description, and restrictions

### Namespace Isolation Architecture
Each agent gets isolated planning/todo storage:
- Planning maintains `_plan_stores: Dict[str, List[Dict]]`
- Todo maintains `_todo_stores: Dict[str, List[Dict]]`
- Namespace format: `"{agent_type}_{agent_id}"`
- Prevents cross-agent conflicts

### Session-Based Project Structure
Each chat session automatically creates a project directory:
- Path: `/outputs/session_{timestamp}/`
- All file operations scoped to session
- No manual project setup needed
- Backend initializes on first user message

### Parallel Task Delegation
- Supervisor analyzes dependencies before delegation
- Multiple tasks delegated simultaneously when possible
- Sub-agents (research/analysis/writing) exposed as async tools
- Dependency tracking prevents premature execution

## Quick Start

### Prerequisites
- Python 3.10+ with virtual environment activated
- Node.js 18+
- PostgreSQL running locally
- MLflow server (optional but recommended)

### 1. Letta Server Setup (Required)

```bash
# Activate virtual environment
source .venv/bin/activate

# Start local Letta server with ADE support
./scripts/dev/start-letta-with-ade.sh
# OR manually:
.venv/bin/letta server --port 8283 --ade --host 0.0.0.0

# Verify server is running
curl http://localhost:8283/v1/health
```

### 2. Backend Setup

```bash
# In a new terminal, activate virtual environment
source .venv/bin/activate

# Start MLflow (optional but recommended)
mlflow server --host 0.0.0.0 --port 5002 &

# Start the backend
cd backend
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
# Install dependencies (including CopilotKit)
cd frontend
npm install

# Start the development server
npm run dev
```

### 4. Access the POC

1. Open http://localhost:3000/poc
2. Click the CopilotKit button (bottom-right)
3. Enter a complex task like:
   - "Analyze the pros and cons of remote work"
   - "Create a market analysis for electric vehicles"
   - "Write a strategic brief on AI in healthcare"

## Architecture

### Agent Hierarchy
```
Global Supervisor (Letta)
├── Research Agent (Letta)
├── Analysis Agent (Letta)
└── Writing Agent (Letta)
```

### Data Flow
1. User enters task in CopilotKit sidebar
2. CopilotKit sends action to `/api/copilotkit`
3. AG-UI bridge translates to Letta agent calls
4. Supervisor orchestrates sub-agents
5. Results stream back through SSE
6. MLflow tracks all LLM interactions

## Key Files

### Backend - Agent Tools
- `backend/src/agents/tools/planning_tool.py` - LLM-based task decomposition
- `backend/src/agents/tools/todo_tool.py` - Task tracking with namespace isolation
- `backend/src/agents/tools/file_tool.py` - Session-scoped file operations
- `backend/src/agents/tools/research_tool.py` - Research agent delegation
- `backend/src/agents/tools/analysis_tool.py` - Analysis agent delegation
- `backend/src/agents/tools/writing_tool.py` - Writing agent delegation
- `backend/src/agents/tools/tool_registry.py` - Central tool registration

### Backend - Core
- `backend/src/agents/agent_factory.py` - Letta agent creation
- `backend/src/agents/atlas_supervisor.py` - Main supervisor (TODO: needs creation)
- `backend/src/agui/copilot_bridge.py` - CopilotKit to AG-UI translation
- `backend/main.py` - FastAPI server with all integrations

### Frontend
- `frontend/src/components/CopilotProvider.tsx` - CopilotKit setup
- `frontend/src/app/poc/page.tsx` - POC demonstration page
- `frontend/src/app/api/copilotkit/route.ts` - Next.js API proxy

## TODO: Complete Supervisor Agent

Create `backend/src/agents/atlas_supervisor.py` with the Letta supervisor agent:

```python
class ATLASSupervisor:
    """
    Main supervisor agent that orchestrates task execution.
    Uses tools for planning, todo management, file operations, and delegation.
    """

    def __init__(self, agent_factory: LettaAgentFactory):
        # Create Letta agent with registered tools
        self.agent = agent_factory.create_supervisor_agent()

    async def process_task(self, user_query: str) -> Dict[str, Any]:
        """
        1. Use planning tool to decompose task
        2. Create todos with dependencies
        3. Delegate to sub-agents based on task_type
        4. Monitor progress and update todos
        5. Aggregate results and return
        """
        # Implementation using registered tools
```

## Environment Variables

Ensure your `.env` file contains:
```
LETTA_API_KEY=your_key_here  # Or leave empty for local mode
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

## Monitoring

- **MLflow UI**: http://localhost:5002
- **Backend API**: http://localhost:8000/docs
- **Agent Status**: http://localhost:8000/api/copilotkit/status/{task_id}

## What's Been Simplified

Moved to `/archive/`:
- Complex database integrations (ChromaDB, Neo4j, Redis)
- Enhanced MLflow tracking layers
- LC-deep-research-UI (separate project)
- Multiple test files
- Advanced agent implementations

Kept Essential:
- Core Letta agent structure
- CopilotKit UI integration
- AG-UI real-time communication
- Basic MLflow tracking
- PostgreSQL for persistence

## Next Steps

1. Implement the `orchestrate_task()` method
2. Test end-to-end flow
3. Add error handling
4. Enhance agent prompts
5. Add more sophisticated task decomposition

## Troubleshooting

### Letta Connection Issues
- Check LETTA_API_KEY in .env
- Verify Letta server is running (if using local mode)

### CopilotKit Not Appearing
- Check browser console for errors
- Verify backend is running on port 8000
- Check CORS settings in main.py

### MLflow Not Tracking
- Ensure MLflow server is running
- Check MLFLOW_TRACKING_URI in environment