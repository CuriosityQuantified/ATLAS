# ATLAS POC Implementation Plan - Tool-Based Architecture

**Created**: September 22, 2025
**Last Updated**: September 23, 2025
**Status**: Phase 2 In Progress
**Architecture**: Tool-Based Supervisor with Local Letta

## Overview
Transform the ATLAS supervisor agent to use a tool-based architecture where sub-agents (Research, Analysis, Writing) are exposed as tools, along with planning, todo management, and file operations. **Letta will run locally, not using cloud API.**

## Phase 1: Dependencies & Local Letta Setup ✅ COMPLETED

### 1.1 Update Dependencies
**File**: `backend/requirements.txt`
- [x] Added `letta>=0.11.0` and `letta-client>=0.1.0`
- [x] Added `sqlite-vec>=0.1.0` for vector support
- [ ] Add `helix-db>=0.1.0` for knowledge storage (Phase 5)
- [ ] Add `e2b-code-interpreter>=0.0.10` for code execution (Phase 4)
- [ ] Add `firecrawl-py>=1.0.0` for web scraping (Phase 4)
- [x] Run `source .venv/bin/activate && uv pip install -r backend/requirements.txt`

### 1.2 Local Letta Server Setup ✅
**Action**: Configured local Letta server with Web ADE support
```bash
# Server running successfully at http://localhost:8283
.venv/bin/letta server --port 8283 --ade --host 0.0.0.0
```

**File**: `backend/src/agents/letta_config.py` ✅
```python
# Configuration for local Letta connection
LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
LETTA_API_KEY = None  # No API key needed for local mode
```

### 1.3 Environment Configuration ✅
**File**: `.env` updates
```
# Letta - LOCAL MODE
LETTA_SERVER_URL=http://localhost:8283
LETTA_LOCAL_MODE=true
# LETTA_API_KEY not needed for local mode
```

## Phase 2: Agent Architecture Implementation 🔄 IN PROGRESS

### 2.1 Session-Based Architecture ✅
**Key Principle**: Each chat session gets an auto-created project directory
- Path format: `/outputs/session_{timestamp}/`
- All file operations automatically scoped to session
- No manual project setup required
- Session initialized by backend on first user message

### 2.2 Supervisor Agent Tools (Streamlined)

#### Planning Tools ✅ COMPLETED
**File**: `backend/src/agents/tools/planning_tool.py`
- [x] `plan_task(task, context, agent_memory)` -> LLM-based planning with:
  - task_type (not agent_type)
  - dependencies (required field)
  - NO priority field
- [x] `update_plan(plan_id, updates, feedback)` -> Modifies existing plan

#### Todo Management ✅ COMPLETED
**File**: `backend/src/agents/tools/todo_tool.py`
- [x] `create_todo(task_id, description, task_type, dependencies)` -> Adds task
- [x] `update_todo_status(task_id, status, result, error)` -> Updates progress
- [x] NO query tools (supervisor maintains full context)

#### File Operations ✅ COMPLETED
**File**: `backend/src/agents/tools/file_tool.py`
- [x] `initialize_session(session_id)` -> Called by backend on chat start
- [x] `save_output(filename, content, file_type, subdirectory)`
- [x] `load_file(filename, subdirectory)`
- [x] `append_content(filename, content, subdirectory)`
- [x] `list_outputs(subdirectory, file_type)`

#### Delegation Tools ✅ COMPLETED
**Files created**:
- [x] `backend/src/agents/tools/research_tool.py`
  - `delegate_research(context, task_description, restrictions)` - XML-structured prompts
  - `get_research_status(agent_id)` - Query research progress
- [x] `backend/src/agents/tools/analysis_tool.py`
  - `delegate_analysis(context, task_description, restrictions)` - XML-structured prompts
  - `get_analysis_status(agent_id)` - Query analysis progress
- [x] `backend/src/agents/tools/writing_tool.py`
  - `delegate_writing(context, task_description, restrictions)` - XML-structured prompts
  - `get_writing_status(agent_id)` - Query writing progress

### 2.3 Namespace Isolation Architecture ✅ NEW
**Key Innovation**: Each agent gets isolated planning/todo storage
- Planning tool maintains `_plan_stores: Dict[str, List[Dict]]`
- Todo tool maintains `_todo_stores: Dict[str, List[Dict]]`
- Namespace format: `"{agent_type}_{agent_id}"` (e.g., `research_abc123`)
- Supervisor uses default namespace (None maps to "supervisor")
- Prevents cross-agent task/plan conflicts

### 2.4 Supervisor Behavior
- Maintains complete plan and todo list in context window
- Analyzes dependencies before delegating tasks
- Delegates multiple tasks in parallel when no dependencies exist
- Never delegates dependent tasks until prerequisites complete
- Emphasis on delegation over direct execution

### 2.5 Sub-Agent Creation with Local Letta
**Updates to agent_factory.py**:
- `create_research_agent()`:
  - Register web_search tool (Firecrawl)
  - Register store_research tool (HelixDB)
- `create_analysis_agent()`:
  - Register run_code tool (E2B)
  - Register read_research tool (HelixDB)
  - Register store_analysis tool (HelixDB)
- `create_writing_agent()`:
  - Register read_knowledge tool (HelixDB)
  - Register file operation tools

### 2.6 Sub-Agent Tool Wrappers (Delegation Tools) ✅ COMPLETED
**File**: `backend/src/agents/tools/research_tool.py`
- Implemented `delegate_research(context, task_description, restrictions)`:
  - Creates/retrieves research agent via LettaAgentFactory
  - Sends XML-structured prompt with context
  - Returns delegation status with agent_id
  - Includes namespace for isolated planning/todo

**File**: `backend/src/agents/tools/analysis_tool.py`
- Implemented `delegate_analysis(context, task_description, restrictions)`:
  - Creates/retrieves analysis agent via LettaAgentFactory
  - Uses same XML prompt structure as research
  - Returns delegation status with agent_id
  - Namespace isolation for independent task tracking

**File**: `backend/src/agents/tools/writing_tool.py`
- Implemented `delegate_writing(context, task_description, restrictions)`:
  - Creates/retrieves writing agent via LettaAgentFactory
  - Consistent XML prompt structure
  - Returns delegation status with agent_id
  - Isolated namespace for writing tasks

## Phase 3: MLflow Integration

### 3.1 Enhanced MLflow Tracking for Agents
**File**: `backend/src/mlflow/agent_tracking.py`
```python
class AgentMLflowTracker:
    """Enhanced tracking for tool-based agent architecture."""

    def track_agent_creation(self, agent_id: str, agent_type: str, tools: list):
        """Log agent creation with tool registration."""
        mlflow.log_param(f"{agent_id}_type", agent_type)
        mlflow.log_param(f"{agent_id}_tools", tools)

    def track_tool_call(self, agent_id: str, tool_name: str, params: dict):
        """Log each tool invocation."""
        mlflow.log_metric(f"{agent_id}_{tool_name}_calls", 1)
        mlflow.log_dict(params, f"tool_calls/{agent_id}_{tool_name}_{timestamp}.json")

    def track_tool_result(self, agent_id: str, tool_name: str, result: dict, duration: float):
        """Log tool execution results and performance."""
        mlflow.log_metric(f"{agent_id}_{tool_name}_duration", duration)
        mlflow.log_dict(result, f"tool_results/{agent_id}_{tool_name}_{timestamp}.json")

    def track_plan(self, plan: dict):
        """Log planning tool output."""
        mlflow.log_dict(plan, "plans/plan_{timestamp}.json")
        mlflow.log_metric("plan_steps", len(plan.get("steps", [])))

    def track_knowledge_operation(self, operation: str, data_size: int):
        """Log HelixDB operations."""
        mlflow.log_metric(f"helix_{operation}_count", 1)
        mlflow.log_metric(f"helix_{operation}_size", data_size)
```

### 3.2 Integration with Supervisor Agent
**Updates to**: `backend/src/agents/supervisor_agent.py`
- Initialize MLflow tracker in constructor
- Track agent creation with tools
- Wrap all tool calls with tracking

### 3.3 MLflow Dashboards for Tool-Based Architecture
**File**: `backend/src/mlflow/dashboards.py`
- Create custom views for:
  - Tool usage frequency by agent
  - Tool execution times
  - Planning effectiveness (steps completed vs planned)
  - Knowledge storage growth over time
  - Cost tracking per tool (especially API-based tools)

### 3.4 Cost Tracking for External Tools
**File**: `backend/src/mlflow/cost_tracking.py`
- Track costs for Firecrawl, E2B, GPT-4/Claude planning
- Aggregate costs per task and per session
- Alert on cost thresholds

## Phase 4: Tool Implementation

### 4.1 Planning Tool (LLM-based)
**File**: `backend/src/agents/tools/planning_tool.py`
- LLM-based planning with GPT-4 or Claude
- Accepts task and full context from supervisor
- Returns structured plan with steps, dependencies, estimates
- **Future**: DSPy optimization (see Future Phases)

### 4.2 Research Tools
**File**: `backend/src/agents/tools/firecrawl_tool.py`
- Web search and scraping via Firecrawl API
- Result formatting with sources
- Local caching to avoid duplicate searches
- Cost and rate limit tracking

### 4.3 Analysis Tools
**File**: `backend/src/agents/tools/e2b_tool.py`
- Code execution in E2B sandbox
- Support for Python, JavaScript, R
- Output and error capture
- Execution time limits

### 4.4 File Operation Tools
**File**: `backend/src/agents/tools/file_tools.py`
- Create, read, update file operations
- Path validation and security
- Automatic backup on updates
- Directory creation as needed

### 4.5 Todo Management Tool
**File**: `backend/src/agents/tools/todo_tool.py`
- Parse and update todo lists in agent memory
- Track completion status
- Priority management
- MLflow metrics for todo completion rates

## Phase 5: HelixDB Knowledge Storage

### 5.1 HelixDB Client Implementation
**File**: `backend/src/agents/database/helix_client.py`
- Local graph database for knowledge storage
- Methods for storing research, analysis, and queries
- Metadata and timestamp tracking
- MLflow integration for operation metrics

### 5.2 HelixDB Integration Tools
**File**: `backend/src/agents/tools/helix_tools.py`
- Wrappers for agent-specific operations
- Research storage and retrieval
- Analysis linking to research
- Knowledge queries for writing agent

## Phase 6: CopilotKit & AG-UI Integration

### 6.1 Update CopilotKit Bridge
**File**: `backend/src/agui/copilot_bridge.py`
- Replace orchestrate_task with tool-based flow
- Stream tool events through AG-UI
- Include MLflow run IDs in responses

### 6.2 AG-UI Event Extensions
**File**: `backend/src/agui/events.py`
New event types:
- TOOL_CALLED
- TOOL_RESULT
- PLAN_CREATED
- PLAN_UPDATED
- KNOWLEDGE_STORED
- TODO_UPDATED
- MLFLOW_METRIC

### 6.3 Frontend Updates
**File**: `frontend/src/app/poc/page.tsx`
- Tool call visualization
- Real-time plan and todo updates
- Knowledge graph display
- MLflow metrics in UI

## Phase 7: Testing & Validation

### 7.1 Unit Testing
- Individual tool testing with mocks
- Agent creation and tool registration
- MLflow tracking verification

### 7.2 Integration Testing
- Agent-to-agent communication
- Knowledge persistence in HelixDB
- File operations
- Cost tracking accuracy

### 7.3 End-to-End Testing
Test scenarios:
1. Research and analysis workflow
2. Technical documentation generation
3. Multi-step planning execution

## Development Checkpoints

- [x] **Checkpoint 1**: Local Letta server running with test agent
- [x] **Checkpoint 2**: Agents created locally with tool stubs (100% complete)
  - [x] Planning, Todo, File tools implemented with namespace isolation
  - [x] Delegation tools created with XML prompt structure
  - [x] All tools registered in tool_registry.py
- [ ] **Checkpoint 3**: MLflow tracking all agent operations
- [ ] **Checkpoint 4**: All tools implemented and tracked
- [ ] **Checkpoint 5**: HelixDB storing and retrieving data locally
- [ ] **Checkpoint 6**: Full workflow executing with complete observability
- [ ] **Checkpoint 7**: CopilotKit UI showing tool execution and metrics

## Future Phases (Post-POC)

### Phase 8: Librarian Agent Implementation
**Purpose**: Intelligent knowledge management and retrieval
- Create Librarian agent as a specialized tool for all agents
- Implement semantic search across all stored knowledge
- Add citation tracking and source verification
- Create knowledge graph visualization
- Implement knowledge pruning and consolidation

### Phase 9: DSPy Planning Optimization
**Purpose**: Improve planning quality and consistency
- Replace LLM prompts with DSPy modules
- Implement ChainOfThought for complex planning
- Use DSPy compiler to optimize prompts
- Add assertion-based plan validation
- Create few-shot example bank
- A/B test DSPy vs standard prompting
- Track improvement metrics in MLflow

### Phase 10: Production Enhancements
- Multi-user support with session isolation
- Agent state persistence and recovery
- Horizontal scaling with multiple Letta servers
- Advanced cost optimization strategies
- Real-time collaboration features

## Local Development Setup

### Required Services
```bash
# Terminal 1: Letta Server (REQUIRED)
source .venv/bin/activate
letta server --port 8283

# Terminal 2: MLflow (REQUIRED)
mlflow server --host 0.0.0.0 --port 5002

# Terminal 3: Backend FastAPI
cd backend
uvicorn main:app --reload --port 8000

# Terminal 4: Frontend
cd frontend
npm run dev
```

### Service URLs
- Letta Server: http://localhost:8283
- MLflow UI: http://localhost:5002
- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:3000/poc

## Key Design Decisions

1. **Local Letta**: Privacy, control, no API costs
2. **Tools as Functions**: Clean separation of concerns
3. **MLflow First**: Observability from the start
4. **HelixDB**: Graph structure for knowledge relationships
5. **Progressive Enhancement**: POC first, optimize later

## Success Criteria

1. **Functional**: Complete task execution through tool calls
2. **Observable**: Full visibility via MLflow
3. **Persistent**: Knowledge retained across sessions
4. **Scalable**: Architecture supports future enhancements
5. **Maintainable**: Clear code structure and documentation

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Letta server crashes | Auto-restart script, state persistence |
| Tool registration fails | Validation before registration, graceful degradation |
| HelixDB corruption | Regular backups, SQLite fallback |
| API rate limits | Caching, exponential backoff, cost alerts |
| Memory overflow | Context window management, memory pruning |

## Notes

- Each phase should be committed separately
- Test incrementally, don't wait for full implementation
- Monitor resource usage (CPU, memory, disk)
- Keep detailed logs for debugging
- Document any deviations from plan

---

**Next Steps**:
1. Review and approve plan
2. Begin Phase 1 implementation
3. Set up local development environment
4. Create initial project structure
