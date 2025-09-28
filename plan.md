# ATLAS POC Implementation Plan - Tool-Based Architecture

**Created**: September 22, 2025
**Last Updated**: January 27, 2025
**Status**: Phase 3 Completed ✅, Phase 4 Ready to Start
**Architecture**: Tool-Based Supervisor with Local Letta

## Overview
Transform the ATLAS supervisor agent to use a tool-based architecture where sub-agents (Research, Analysis, Writing) are exposed as tools, along with planning, todo management, and file operations. **Letta will run locally, not using cloud API.**

## Recent Updates (January 27, 2025)
- ✅ Switched from OpenRouter to OpenAI models for full Letta compatibility
- ✅ Implemented comprehensive .gitignore and .env.example
- ✅ Successfully tested all agent types with OpenAI integration
- ✅ Force-pushed clean codebase to GitHub
- ✅ Fixed all Letta API compatibility issues (retrieve, create, ReasoningMessage)
- ✅ Completed Phase 3: MLflow Integration with 5/5 tests passing

## Phase 1: Dependencies & Local Letta Setup ✅ COMPLETED

### 1.1 Update Dependencies ✅
**File**: `backend/requirements.txt`
- [x] Added `letta>=0.11.0` and `letta-client>=0.1.0`
- [x] Added `sqlite-vec>=0.1.0` for vector support
- [x] Added `mlflow>=3.0.0` for tracking
- [ ] Add `helix-db>=0.1.0` for knowledge storage (Phase 5)
- [ ] Add `e2b-code-interpreter>=0.0.10` for code execution (Phase 4)
- [ ] Add `firecrawl-py>=1.0.0` for web scraping (Phase 4)
- [x] Installed all dependencies with `uv pip install`

### 1.2 Local Letta Server Setup ✅
**Action**: Configured local Letta server with Web ADE support
```bash
# Server running successfully at http://localhost:8283
.venv/bin/letta server --port 8283 --ade --host 0.0.0.0
```

**File**: `backend/src/agents/letta_config.py` ✅
- Successfully implemented local server configuration
- Health check and ADE connection info functions
- Environment validation

### 1.3 Environment Configuration ✅
**File**: `.env.example` - Comprehensive template created
- OpenAI API keys for models and embeddings
- Letta local mode configuration
- Database configurations
- MLflow settings
- Feature flags

## Phase 2: Agent Architecture Implementation ✅ COMPLETED

### 2.1 Session-Based Architecture ✅
**Key Principle**: Each chat session gets an auto-created project directory
- Path format: `/outputs/session_{timestamp}/`
- All file operations automatically scoped to session
- No manual project setup required
- Session initialized by backend on first user message

### 2.2 Model Integration (Updated) ✅

#### OpenAI Configuration ✅ NEW
**File**: `backend/src/config/openai_config.py`
- Created OpenAIConfig class with model hierarchy:
  - **Supervisor**: GPT-4o (complex reasoning)
  - **Writing**: GPT-4o (high-quality output)
  - **Research**: GPT-4o-mini (cost-effective)
  - **Analysis**: GPT-4o-mini (cost-effective)
- **Embeddings**: text-embedding-3-small (1536 dimensions)
- Cost tracking built into configuration

#### Agent Factory Updates ✅
**File**: `backend/src/agents/agent_factory.py`
- [x] Updated all agent creation methods to use OpenAI models
- [x] Proper API key configuration for LLM and embeddings
- [x] Removed OpenRouter dependencies (preserved in config for future)
- [x] All agent types tested and working

### 2.3 Supervisor Agent Tools ✅

#### Planning Tools ✅ COMPLETED
**File**: `backend/src/agents/tools/planning_tool.py`
- [x] `plan_task(task, context, agent_memory)` -> LLM-based planning
- [x] `update_plan(plan_id, updates, feedback)` -> Modifies existing plan
- [x] Namespace isolation for multi-agent support

#### Todo Management ✅ COMPLETED
**File**: `backend/src/agents/tools/todo_tool.py`
- [x] `create_todo(task_id, description, task_type, dependencies)`
- [x] `update_todo_status(task_id, status, result, error)`
- [x] Full context maintained in supervisor memory

#### File Operations ✅ COMPLETED
**File**: `backend/src/agents/tools/file_tool.py`
- [x] `initialize_session(session_id)` -> Auto-creates session directory
- [x] `save_output(filename, content, file_type, subdirectory)`
- [x] `load_file(filename, subdirectory)`
- [x] `append_content(filename, content, subdirectory)`
- [x] `list_outputs(subdirectory, file_type)`

#### Delegation Tools ✅ COMPLETED
**Files created**:
- [x] `backend/src/agents/tools/research_tool.py`
- [x] `backend/src/agents/tools/analysis_tool.py`
- [x] `backend/src/agents/tools/writing_tool.py`
- All tools use XML-structured prompts and namespace isolation

### 2.4 Namespace Isolation Architecture ✅
- Each agent gets isolated planning/todo storage
- Namespace format: `"{agent_type}_{agent_id}"`
- Prevents cross-agent task/plan conflicts

### 2.5 Testing & Validation ✅

#### OpenAI Integration Testing ✅ NEW
**File**: `backend/tests/test_openai_integration.py`
- [x] Configuration module tests
- [x] Agent creation with OpenAI models
- [x] Message sending and receiving
- [x] All agent types (supervisor, research, analysis, writing)
- **Result**: 3/3 tests passing

#### OpenRouter Testing (Archived) ✅
**File**: `backend/tests/test_openrouter_configurations.py`
- Comprehensive test suite with 13 configuration approaches
- Discovered Letta authentication issues with OpenRouter
- Code preserved for future when Letta adds proper support

## Phase 3: MLflow Integration ✅ COMPLETED (January 27, 2025)

### 3.1 Enhanced MLflow Tracking for Agents ✅
**File**: `backend/src/mlflow/agent_tracking.py`
- [x] Implemented AgentMLflowTracker class
- [x] Track agent creation with tools
- [x] Log tool invocations and results
- [x] Track planning outputs
- [x] Monitor knowledge operations

### 3.2 Integration with Supervisor Agent ✅
**Updates to**: `backend/src/agents/supervisor.py`
- [x] Initialize MLflow tracker in constructor
- [x] Track agent creation with tools
- [x] Wrap all tool calls with tracking
- [x] Added cleanup method for closing MLflow session

### 3.3 MLflow Dashboards ✅
**File**: `backend/src/mlflow/dashboards.py`
- [x] Tool usage frequency by agent
- [x] Tool execution times
- [x] Planning effectiveness metrics
- [x] Cost tracking per tool
- [x] Agent performance comparison

### 3.4 Cost Tracking ✅
**File**: `backend/src/mlflow/cost_tracking.py`
- [x] Track OpenAI API costs with accurate pricing
- [x] Aggregate costs per task and session
- [x] Alert on cost thresholds
- [x] Token efficiency metrics
- [x] Daily cost projections

## Phase 4: Tool Implementation (External Services)

### 4.1 Research Tools
**File**: `backend/src/agents/tools/firecrawl_tool.py`
- [ ] Web search and scraping via Firecrawl API
- [ ] Result formatting with sources
- [ ] Local caching to avoid duplicate searches

### 4.2 Analysis Tools
**File**: `backend/src/agents/tools/e2b_tool.py`
- [ ] Code execution in E2B sandbox
- [ ] Support for Python, JavaScript, R
- [ ] Output and error capture

### 4.3 Enhanced Planning
- [ ] Consider DSPy optimization for planning tool
- [ ] A/B testing of prompt strategies

## Phase 5: HelixDB Knowledge Storage

### 5.1 HelixDB Client Implementation
**File**: `backend/src/agents/database/helix_client.py`
- [ ] Local graph database setup
- [ ] Knowledge storage and retrieval methods
- [ ] Metadata tracking

### 5.2 HelixDB Integration Tools
**File**: `backend/src/agents/tools/helix_tools.py`
- [ ] Research storage and retrieval
- [ ] Analysis linking to research
- [ ] Knowledge queries for writing agent

## Phase 6: CopilotKit & AG-UI Integration

### 6.1 Update CopilotKit Bridge
**File**: `backend/src/agui/copilot_bridge.py`
- [ ] Replace orchestrate_task with tool-based flow
- [ ] Stream tool events through AG-UI
- [ ] Include MLflow run IDs in responses

### 6.2 AG-UI Event Extensions
**File**: `backend/src/agui/events.py`
- [ ] Add new event types for tools
- [ ] Plan and todo update events
- [ ] Knowledge storage events

### 6.3 Frontend Updates
**File**: `frontend/src/app/poc/page.tsx`
- [ ] Tool call visualization
- [ ] Real-time plan and todo updates
- [ ] MLflow metrics display

## Phase 7: End-to-End Testing

### 7.1 Integration Testing
- [ ] Agent-to-agent communication
- [ ] Knowledge persistence
- [ ] Cost tracking accuracy

### 7.2 Workflow Testing
- [ ] Research and analysis workflow
- [ ] Technical documentation generation
- [ ] Multi-step planning execution

## Development Checkpoints

- [x] **Checkpoint 1**: Local Letta server running with test agent
- [x] **Checkpoint 2**: Agents created locally with OpenAI models (100% complete)
  - [x] Planning, Todo, File tools implemented
  - [x] Delegation tools created with XML prompts
  - [x] All tools registered and working
  - [x] OpenAI integration fully tested
- [x] **Checkpoint 3**: MLflow tracking all agent operations (100% complete)
  - [x] Agent creation and tool tracking
  - [x] Cost tracking with OpenAI pricing
  - [x] Dashboard generation and reporting
  - [x] Integration tests passing (5/5 - All tests passing!)
- [ ] **Checkpoint 4**: External tools (Firecrawl, E2B) integrated
- [ ] **Checkpoint 5**: HelixDB storing and retrieving data
- [ ] **Checkpoint 6**: Full workflow with complete observability
- [ ] **Checkpoint 7**: CopilotKit UI showing tool execution

## Current Implementation Status

### ✅ Completed
1. **Local Letta Server**: Running at http://localhost:8283
2. **OpenAI Integration**: All agents using GPT-4o/GPT-4o-mini
3. **Agent Factory**: Creating agents with proper configurations
4. **Tool Architecture**: Planning, todo, file, and delegation tools
5. **Testing Suite**: Comprehensive tests for OpenAI integration
6. **Repository Structure**: Clean .gitignore and .env.example
7. **MLflow Tracking**: Complete agent tracking with tools and planning
8. **Cost Tracking**: OpenAI API cost monitoring with accurate pricing
9. **Dashboard Generation**: MLflow dashboards and reporting
10. **Letta API Fixes**: All API compatibility issues resolved

### 🔄 In Progress
- None - Ready for Phase 4

### 📋 Next Steps
1. Add Firecrawl for web research (Phase 4.1)
2. Add E2B for code execution (Phase 4.2)
3. Set up HelixDB for knowledge storage (Phase 5)
4. Integrate with CopilotKit & AG-UI (Phase 6)

## Key Architecture Decisions

1. **OpenAI Models**: Switched from OpenRouter for Letta compatibility
2. **Local Letta**: Privacy, control, no cloud API costs
3. **Tools as Functions**: Clean separation of concerns
4. **MLflow First**: Observability from the start
5. **Progressive Enhancement**: POC first, optimize later

## Local Development Setup

### Required Services
```bash
# Terminal 1: Letta Server (REQUIRED)
source .venv/bin/activate
letta server --port 8283 --ade --host 0.0.0.0

# Terminal 2: MLflow (OPTIONAL - for tracking)
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
- Letta Web ADE: https://app.letta.com (connect to local server)
- MLflow UI: http://localhost:5002
- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:3000/poc

## Repository Information
- **GitHub**: https://github.com/CuriosityQuantified/ATLAS
- **Latest Commit**: Major refactor with OpenAI models
- **Status**: Clean baseline established, ready for Phase 3

## Notes

- Each phase should be committed separately
- Test incrementally with each major change
- Monitor OpenAI API usage and costs
- Document any deviations from plan
- OpenRouter code preserved for future integration

---

**Next Steps**:
1. Begin Phase 3: MLflow Integration
2. Enhance cost tracking for OpenAI usage
3. Prepare for external tool integration (Firecrawl, E2B)