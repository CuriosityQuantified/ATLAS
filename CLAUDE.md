Note: Always use absolute path references for imports, not relative path imports

## Project Overview

ATLAS (Agentic Task Logic & Analysis System) is a hierarchical multi-agent system designed for modular reasoning and structured content generation. The system decomposes complex tasks into specialized sub-processes managed by autonomous but coordinated agent teams.

## 📍 Current Working Directory

**Current Location**: `/Users/nicholaspate/Documents/01_Active/ATLAS`
**Virtual Environment**: `/Users/nicholaspate/Documents/01_Active/ATLAS/.venv`
**Last Updated**: 2025-09-22 (Planning Phase - Tool-Based Architecture)

**Active Services:**
- Letta Server: http://localhost:8283 (Local agent runtime)
- Backend API: http://localhost:8000 (FastAPI with AG-UI)
- Frontend UI: http://localhost:3000/poc (CopilotKit integration)
- MLflow: http://localhost:5002 (Observability and tracking)

**🏗️ Architecture Status (Tool-Based POC):**
- Supervisor Agent: Tool-based architecture planned
- Research Agent: Exposed as tool with Firecrawl web search
- Analysis Agent: Exposed as tool with E2B code execution
- Writing Agent: Exposed as tool with file operations
- Knowledge Storage: HelixDB for shared agent memory
- Frontend: CopilotKit with AG-UI real-time updates
- MLflow: Comprehensive tool call tracking

**Directory Navigation Notes:**
- Always update this section when changing directories
- Backend server files located at: `/Users/nicholaspate/Documents/ATLAS/backend/`
- Frontend files located at: `/Users/nicholaspate/Documents/ATLAS/frontend/`

## 🤝 Collaborative Development Approach

**IMPORTANT**: We are coding together as a team. You must:
1. **NEVER implement code without explicit approval** - Always discuss architecture, class design, function signatures, and variable naming BEFORE writing code
2. **Always ask questions** about design choices, trade-offs, and implementation details
3. **Explain your reasoning** for technical decisions to help the user learn
4. **Seek confirmation** before making any changes to existing code
5. **Discuss alternatives** when multiple approaches are possible

The goal is for the user to:
- Deeply understand every aspect of the codebase
- Learn best practices and design patterns
- Be able to modify and extend the code independently
- Make informed decisions about architecture choices

## ⚠️ CRITICAL: Virtual Environment Usage

**ALWAYS use the virtual environment for Python development:**

```bash
# Activate virtual environment (REQUIRED before any Python commands)
source .venv/bin/activate

# Verify activation (should show .venv path)
which python
```

**When Claude Code runs Python commands:**
1. **ALWAYS** activate `.venv` first: `source .venv/bin/activate && python ...`
2. **NEVER** run `python` or `pip` commands without activation
3. **ALWAYS** use `uv` for package management when possible
4. **CHECK** activation with `which python` to confirm `.venv` path

**CRITICAL: LangGraph Deep Agents Commands (DOCUMENT FOR FUTURE REFERENCE):**
```bash
# ALWAYS use full venv path for LangGraph to avoid Python version issues
cd /Users/nicholaspate/Documents/01_Active/ATLAS/LC-deep-research-UI/deepagents/examples/research
/Users/nicholaspate/Documents/01_Active/ATLAS/.venv/bin/langgraph dev

# Installing deepagents (MUST use uv, not pip)
cd /Users/nicholaspate/Documents/01_Active/ATLAS/LC-deep-research-UI/deepagents
source /Users/nicholaspate/Documents/01_Active/ATLAS/.venv/bin/activate && uv pip install -e .

# Kill existing LangGraph if port is in use
pkill -f "langgraph dev"
lsof -i :2024 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null
```

**Common Mistakes to Avoid:**
- Running `python script.py` without activation (uses system Python)
- Installing packages with `pip install` instead of `uv pip install`
- Forgetting to include `source .venv/bin/activate &&` in bash commands
- Using `langgraph dev` without full venv path (causes Python version errors)

## Architecture

### Tool-Based Architecture (Phase 2 Implementation)

**Supervisor Agent Tools**:
- **Planning Tools**:
  - `plan_task`: Decomposes tasks with dependencies (no priority field, uses task_type not agent_type)
  - `update_plan`: Modifies plans based on execution feedback
- **Todo Management** (Minimal):
  - `create_todo`: Adds tasks with dependency tracking
  - `update_todo_status`: Updates progress (pending/in_progress/completed/failed)
- **File Operations** (Session-scoped):
  - `save_output`: Writes to session directory
  - `load_file`: Reads from session directory
  - `append_content`: Incremental updates
  - `list_outputs`: Shows session files
- **Delegation Tools** (Async-capable):
  - `delegate_research`: Sends tasks to research agent
  - `delegate_analysis`: Sends tasks to analysis agent
  - `delegate_writing`: Sends tasks to writing agent

**Key Design Principles**:
- Supervisor maintains complete plan/todo context (no query tools needed)
- Session directories auto-created on chat initialization
- Parallel delegation when no dependencies exist
- All sub-agent tools support async execution
- Dependencies explicitly tracked and enforced

### Key Architectural Patterns
- **Tools as Functions**: Each capability exposed as a callable tool
- **Local Letta Runtime**: Agents run locally, not cloud API
- **Shared Knowledge**: HelixDB graph database for inter-agent memory
- **Observable Execution**: MLflow tracks every tool call
- **Real-time Updates**: AG-UI streams tool events to frontend

## Development Status

**Current Phase**: Phase 2 - Agent Architecture Implementation (September 23, 2025)

**Phase 1**: ✅ COMPLETED - Local Letta server running at http://localhost:8283

**Phase 2 Architecture** (90% COMPLETE):
✅ **Completed**:
- **Session-Based Projects**: Each chat session gets auto-created directory `/outputs/session_{timestamp}/`
- **Planning & Todo Tools**: LLM-based planning with namespace isolation
- **File Operations**: Session-scoped save/load/append/list functions
- **Delegation Tools**: XML-structured prompts for research/analysis/writing agents
- **Namespace Isolation**: Each agent gets isolated planning/todo storage
- **Tool Registry**: All tools registered and ready for use

🔄 **Remaining**:
- **Atlas Supervisor Agent**: Create main supervisor using Letta with registered tools
- **Agent Factory Updates**: Implement create_supervisor_agent() method
- **Integration Testing**: Verify end-to-end tool execution flow

**Implementation Plan**: See `PLAN.md` for detailed 7-phase implementation:
1. ✅ Dependencies & Local Letta Setup (COMPLETE)
2. 🔄 Agent Architecture Implementation (IN PROGRESS)
3. MLflow Integration
4. Tool Implementation
5. HelixDB Knowledge Storage
6. CopilotKit & AG-UI Integration
7. Testing & Validation

**Future Enhancements** (Post-POC):
- Phase 8: Librarian Agent for knowledge management
- Phase 9: DSPy optimization for planning tool
- Phase 10: Production enhancements

**Current Focus**: Streamlined POC with tool-based architecture. Complex features archived in `/archive/` for future reference.

**Important**: We are working in the virtual environment due to Docker networking challenges with MLflow. All database services will be installed and configured locally.

## 🔧 MLflow Architecture Restoration (2025-01-03)

**Issue Resolved**: Fixed "GlobalSupervisorAgent object has no attribute 'mlflow_tracker'" errors that occurred after previous consolidation changes.

### ✅ Restoration Actions Completed

**1. Restored MLflow Tracking Files**:
- Created `backend/src/mlflow/tracking.py` - Original ATLASMLflowTracker class with core tracking functionality
- Created `backend/src/mlflow/enhanced_tracking.py` - EnhancedATLASTracker class with comprehensive LLM and tool call monitoring
- Updated `backend/src/mlflow/__init__.py` - Clean imports for both tracking systems

**2. Fixed Agent Parameter Handling**:
- Updated `GlobalSupervisorAgent.__init__()` to accept `mlflow_tracker` parameter
- Updated `LibraryAgent.__init__()` to accept `mlflow_tracker` parameter
- Enhanced `BaseAgent.__init__()` to properly store and use `mlflow_tracker`

**3. Enhanced Agent Integration**:
- Agent status changes now log to both enhanced and legacy trackers
- Tool calls (library operations) log comprehensive metadata
- Agent communications (delegations) tracked with full context
- System prompts (YAML personas) automatically logged on agent initialization

**4. API Endpoint Updates**:
- `backend/src/api/agent_endpoints.py` now initializes agents with EnhancedATLASTracker
- Task creation properly sets up MLflow experiments and runs
- Enhanced tracking captures complete task lifecycle

### 📊 Enhanced Tracking Capabilities

Comprehensive monitoring system tracking YAML persona content, conversation history, LLM interactions with multi-provider support, agent state transitions, tool calls, inter-agent communications, and performance analytics including cost tracking, token usage, processing times, and success rates.

### 🏗️ Architecture Principles Maintained

**Separation of Concerns**: MLflow tracking logic kept in dedicated modules, not mixed into core agent functionality

**Backward Compatibility**: All existing agent code works without modification

**Clean Dependencies**: Agents accept optional mlflow_tracker parameter, gracefully handle None values

**Enhanced Capabilities**: New tracking features added without breaking existing functionality

### 🧪 Testing & Validation

**Test Files**:
- `test_simple_restoration.py` - Validates basic agent initialization without errors
- `test_restored_architecture.py` - Comprehensive tracking functionality test
- `test_frontend_backend_mlflow.py` - End-to-end API integration test

**Success Criteria Met**:
- ✅ No mlflow_tracker attribute errors
- ✅ Agents initialize with enhanced tracking
- ✅ MLflow dashboard shows comprehensive data
- ✅ Original architecture patterns preserved

### Database Work Progress
- **Schema Design**: ✅ Completed with foreign key relationships and hybrid memory storage
- **PostgreSQL Setup**: ✅ COMPLETED - 3 databases created (atlas_main, atlas_agents, atlas_memory) with full schema initialization
- **Database Users**: ✅ COMPLETED - postgres superuser created, database-specific users with proper ownership
- **Connection Testing**: ✅ COMPLETED - 7/7 tests passing, all CRUD operations validated
- **File Storage**: 🔄 Database references implemented, local filesystem paths configured
- **Redis Configuration**: 🔄 IN PROGRESS - caching and pub/sub setup
- **ChromaDB Setup**: ⏳ Pending - vector embeddings for agent memory and documents
- **Neo4j Configuration**: ⏳ Pending - knowledge graph for project relationships

### Critical Database Setup Learnings
**UV Package Management**: This project uses `uv` for virtual environments. Always use `uv pip install` instead of `pip install`.

**PostgreSQL Reproducibility**: Created standard `postgres` superuser with `createuser -s postgres` for consistent setup across environments.

**Database Permissions**: Users require database ownership (`ALTER DATABASE atlas_main OWNER TO atlas_main_user`) and schema permissions for table creation.

**Path Dependencies**: PostgreSQL tools must be in PATH during psycopg2-binary installation: `export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"`

## Deployment Strategy

### Recommended Architecture: Containerized Deployment
Based on comprehensive research, ATLAS will use containerized deployment with managed Kubernetes:

**Primary Deployment Options:**
- **AWS EKS** - Best overall ecosystem integration
- **Google GKE** - Superior AI/ML tooling
- **Azure AKS** - Strong enterprise features

**Why Containerized over Serverless:**
- Vercel: ❌ Lacks multi-service support, no WebSocket capability
- Lovable: ❌ Limited to simple web apps, no multi-service architecture
- Kubernetes: ✅ Perfect alignment with ATLAS requirements

**Cost-Optimized Scaling:**
- Development: $300-600/month
- Production: $800-2500/month
- Spot instances for worker agents (up to 90% savings)
- Reserved instances for supervisor agents and databases

## Planned Technologies

### MCP (Model Context Protocol) Servers
The system integrates various MCP servers for enhanced tooling:

**Currently Active:**
- **DeepWiki** - Primary source for code documentation, API references, and best practices (GLOBALLY INSTALLED)

**Planned Integrations:**
- Neo4j for knowledge graphs
- GitHub for version control operations
- Firecrawl for web scraping
- Office integration (PowerPoint, Excel)
- Notion, YouTube, and other platform integrations

**Agent Documentation Strategy:**
All ATLAS agents (Global Supervisor, Team Supervisors, Worker Agents) must:
1. Prioritize DeepWiki MCP for technical documentation searches
2. Use DeepWiki before WebSearch for framework/library information
3. Combine multiple sources (DeepWiki → WebSearch → WebFetch) for comprehensive research

### 🚀 CallModel - Unified LLM Interface
Comprehensive unified model interface with multi-provider support (Anthropic 0.8s, Groq 0.2s, OpenAI 4.0s, Google, HuggingFace, OpenRouter), automatic provider detection, concurrent processing, comprehensive AG-UI + MLflow tracking, DRY architecture, fallback strategies, and performance monitoring.

### Output Formats
Structured JSON, mind maps (Freeplane-compatible), Neo4j knowledge graphs, audio/podcast generation.

## Environment Configuration

Required API keys and settings (stored in `.env`):

### API Keys
- `LETTA_API_KEY` - Letta memory service
- `ANTHROPIC_API_KEY` - Claude models
- `OPENAI_API_KEY` - GPT models
- `GROQ_API_KEY` - Groq fast inference
- `GOOGLE_API_KEY` - Gemini models
- `TAVILY_API_KEY` - Web search
- `GITHUB_API_KEY` - GitHub integration
- `FIRECRAWL_API_KEY` - Web scraping

### Database Configuration
- `POSTGRES_HOST=localhost`
- `POSTGRES_PORT=5432`
- `POSTGRES_DB=atlas_main`
- `POSTGRES_USER=atlas`
- `POSTGRES_PASSWORD=atlas_password`
- `REDIS_URL=redis://localhost:6379`
- `CHROMADB_URL=http://localhost:8000`
- `NEO4J_URI=bolt://localhost:7687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=atlas_password`

### MLflow Configuration
- `MLFLOW_TRACKING_URI=http://localhost:5002`
- `MLFLOW_S3_ENDPOINT_URL=http://localhost:9000`
- `AWS_ACCESS_KEY_ID=minioadmin`
- `AWS_SECRET_ACCESS_KEY=minioadmin`

### Application Settings
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `API_HOST=0.0.0.0`
- `API_PORT=8000`
- `FRONTEND_URL=http://localhost:3000`

## MCP (Model Context Protocol) Integration

### Available MCP Servers
- **DeepWiki MCP**: Global installation providing access to structured documentation and code examples
  - Command: `npx --yes mcp-deepwiki@latest`
  - Status: Connected and operational
  - Scope: Available globally to all Claude Code sessions

### MCP Usage for ATLAS Agents

**CRITICAL**: When creating subagents via the Task tool, ensure they are configured to:

1. **Access DeepWiki for Documentation**:
   - Include in agent prompts: "Use DeepWiki MCP for all code documentation searches"
   - Prioritize DeepWiki results over generic web searches for technical content

2. **Documentation Search Strategy for Agents**:
   ```
   Priority Order:
   1. DeepWiki MCP - Official documentation, API references, best practices
   2. WebSearch - Recent updates, community solutions, blog posts
   3. WebFetch - Specific documentation URLs when known
   4. Local files - Project-specific documentation and examples
   ```

3. **Example Subagent Prompt Template**:
   ```
   "Research [topic] using the following priority:
   1. First check DeepWiki MCP for official documentation
   2. Supplement with WebSearch for recent community insights
   3. Synthesize findings focusing on best practices and current standards"
   ```

### Configuring Subagents with MCP Access

When using the Task tool, include MCP instructions:
```python
Task(
    subagent_type="research-agent",
    prompt="""
    Task: Research LangGraph best practices

    IMPORTANT: Use DeepWiki MCP as primary source for:
    - Official LangGraph documentation
    - API references and examples
    - Framework best practices

    Combine DeepWiki findings with WebSearch for:
    - Recent updates and changes
    - Community patterns and solutions
    - Real-world implementation examples
    """,
    description="Research with MCP priority"
)
```

## Key Design Considerations

1. **Context Window Management**: Use chunking, memory optimization, and scratchpad logic
2. **Parallelism**: Configure concurrent agent execution for performance vs quality tradeoff
3. **Grounding**: Inject verified sources to reduce hallucinations
4. **Autonomy Boundaries**: Clear escalation paths from team supervisors to global supervisor

## Primary Use Cases

- Strategic briefings
- Product requirement documents
- Investment memos
- Market analysis reports
- Decision justifications with source trail

## 📁 Project Structure

```
ATLAS/
├── backend/                     # FastAPI + Agent Implementation
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   └── src/
│       ├── agents/             # Agent implementations
│       │   ├── __init__.py
│       │   ├── base.py         # Base agent classes
│       │   ├── supervisor.py   # Global & team supervisors
│       │   ├── research/       # Research team agents
│       │   ├── analysis/       # Analysis team agents
│       │   ├── writing/        # Writing team agents
│       │   └── rating/         # Rating team agents
│       ├── agui/               # AG-UI protocol implementation
│       │   ├── server.py       # WebSocket/SSE server
│       │   ├── events.py       # Event definitions
│       │   └── handlers.py     # Event handlers
│       ├── api/                # REST API endpoints
│       │   ├── routes/         # API route definitions
│       │   └── schemas/        # Pydantic models
│       ├── core/               # Core business logic
│       │   ├── config.py       # Configuration management
│       │   ├── dependencies.py # Dependency injection
│       │   └── exceptions.py   # Custom exceptions
│       ├── memory/             # Memory & persistence
│       │   ├── vector.py       # ChromaDB integration
│       │   ├── graph.py        # Neo4j integration
│       │   ├── cache.py        # Redis caching
│       │   └── letta.py        # Letta memory management
│       ├── mlflow/             # MLflow monitoring
│       │   ├── tracking.py     # Agent tracking implementation
│       │   ├── config/         # MLflow configuration
│       │   └── src/            # MLflow utilities
│       │       ├── alerts/     # Alert management
│       │       ├── dashboards/ # Dashboard definitions
│       │       └── integrations/ # Third-party integrations
│       ├── orchestration/      # LangGraph orchestration
│       │   ├── graphs.py       # State graph definitions
│       │   ├── states.py       # State management
│       │   └── checkpoints.py  # Checkpointing logic
│       └── utils/              # Shared utilities
│           ├── call_model.py   # 🚀 Unified model interface with tracking
│           ├── cost_calculator.py # LLM cost tracking
│           ├── logging.py      # Structured logging
│           └── validators.py   # Input validation
│
├── frontend/                    # Next.js Dashboard
│   ├── package.json            # Node dependencies
│   ├── next.config.js          # Next.js configuration
│   ├── reference-design/       # Original design prototype (PRESERVE)
│   │   ├── index.html          # Complete HTML dashboard structure
│   │   ├── style.css           # Dark theme CSS with glassmorphism
│   │   └── app.js              # Vanilla JS interactions
│   └── src/
│       ├── app/                # App router pages
│       │   ├── layout.tsx      # Root layout
│       │   ├── page.tsx        # Main dashboard
│       │   ├── globals.css     # Dark theme + glassmorphism styles
│       │   └── api/            # API routes (if needed)
│       ├── components/         # React components
│       │   ├── Dashboard.tsx   # Main dashboard layout
│       │   ├── Sidebar.tsx     # Left navigation sidebar
│       │   ├── AgentArchitecture.tsx # Multi-agent grid visualization
│       │   ├── AgentCard.tsx   # Individual agent status cards
│       │   ├── QuestionsPanel.tsx # Right sidebar agent questions
│       │   └── ChatBar.tsx     # Bottom communication interface
│       ├── lib/                # Frontend utilities
│       │   ├── agui-client.ts  # AG-UI client (future)
│       │   ├── api.ts          # API client (future)
│       │   └── utils.ts        # Helper functions (future)
│       └── types/              # TypeScript definitions
│           └── index.ts        # Agent, Task, Message types
│
├── mlflow/                      # MLflow Monitoring Setup
│   ├── requirements.txt        # MLflow-specific deps
│   ├── dashboards/             # Custom dashboards
│   └── experiments/            # Experiment configs
│
├── infrastructure/              # Docker & Deployment
│   ├── docker-compose.yml      # Local development
│   ├── docker/                 # Docker configurations
│   │   ├── mlflow/            # MLflow Dockerfile
│   │   ├── postgres/          # PostgreSQL init scripts
│   │   └── scripts/           # Setup scripts
│   └── k8s/                    # Kubernetes manifests
│       ├── base/              # Base configurations
│       ├── dev/               # Development overlays
│       └── prod/              # Production overlays
│
├── scripts/                     # Build & utility scripts
│   ├── setup/                  # Setup scripts
│   │   └── install-deps.sh    # Install all dependencies
│   ├── dev/                    # Development scripts
│   │   ├── start-dev.sh       # Start dev environment
│   │   └── watch.sh           # File watchers
│   ├── build/                  # Build scripts
│   │   └── build-all.sh      # Build all services
│   └── utils/                  # Utility scripts
│       └── health-check.sh    # Service health checks
│
├── shared/                      # Shared configurations
│   ├── types/                  # Shared TypeScript types
│   └── schemas/                # Shared data schemas
│
├── docs/                        # Documentation
│   ├── plan.md                 # Development plan
│   ├── architecture/           # Architecture docs
│   ├── design/                 # Design documents
│   ├── guides/                 # Implementation guides
│   └── research/               # Research & analysis
│
├── tests/                       # Integration tests
│   ├── e2e/                    # End-to-end tests
│   └── integration/            # Service integration tests
│
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Root docker compose
├── package.json                 # Root package.json
├── README.md                    # Project overview
└── CLAUDE.md                    # This file (AI guidance)
```

## Development Plan

### Step 1: Docker & MLflow3 Setup ✅
1. Docker infrastructure with all services
2. MLflow3 monitoring integration
3. Cost tracking utilities
4. Health check scripts

### Step 2: Frontend with Endpoints
1. Next.js project setup
2. Dashboard layout with agent visualization
3. API client implementation
4. Real-time update endpoints

### Step 3: AG-UI Configuration
1. WebSocket/SSE server implementation
2. Event protocol definition
3. Frontend client integration
4. Bidirectional communication testing

### Step 4: Backend with LangGraph & Letta
1. Base agent classes
2. Team supervisor implementations
3. LangGraph orchestration
4. Letta memory integration
5. Tool coordination patterns

## Dependency Management

**CRITICAL WORKFLOW**: Always update documentation first, then install from documented requirements.

### Project Dependency Files
1. **Root Package Management**: `./package.json` - Root workspace configuration and scripts
2. **Backend Python Dependencies**: `./backend/requirements.txt` - FastAPI, database drivers, ML libraries
3. **Frontend Node Dependencies**: `./frontend/package.json` - Next.js, React, UI components
4. **Development Scripts**: `./scripts/dev/requirements.txt` - MLflow, testing utilities

### Backend Dependencies (`./backend/requirements.txt`)
FastAPI, uvicorn, websockets, mlflow, psycopg2-binary, redis, chromadb, neo4j, langchain, langgraph, anthropic, openai, groq, google-generativeai, python-dotenv, requests, pydantic, httpx, aiofiles.

### Frontend Dependencies (`./frontend/package.json`)
Next.js 14.2, React 18, Heroicons, Tailwind utilities, react-markdown, remark-gfm, react-syntax-highlighter, TypeScript, ESLint.

### Prerequisites Installation
```bash
brew install postgresql@15 redis neo4j
brew services start postgresql@15
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
createuser -s postgres
```

### Installation Workflow
```bash
source .venv/bin/activate && which python
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
uv pip install -r backend/requirements.txt
cd frontend && npm install
```

### Virtual Environment Troubleshooting
**Key Learnings for Continuous Improvement:**

1. **UV vs PIP Package Management**: This project uses `uv` for virtual environment creation and package management
   - Virtual environment was created with `uv` (confirmed by `/Users/nicholaspate/Documents/ATLAS/.venv/pyvenv.cfg` showing `uv = 0.7.7`)
   - Standard `pip` is not installed in uv-created virtual environments
   - **Solution**: Use `uv pip install` instead of `pip install` for all package installations

2. **PostgreSQL PATH Requirements**: psycopg2-binary requires PostgreSQL tools (pg_config) to be in PATH
   - **Required**: `export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"` before installing psycopg2-binary
   - **Alternative**: Could set environment variables permanently in shell profile

3. **Python Version Mismatch Prevention**:
   - Virtual environment uses Python 3.12.7 (`/Users/nicholaspate/Documents/ATLAS/.venv/bin/python`)
   - System commands may default to Python 3.9 (`/Users/nicholaspate/Library/Python/3.9/lib/python/site-packages`)
   - **Solution**: Always use virtual environment activation and verify with `which python`

4. **Package Installation Best Practices**:
   - ✅ **Correct**: `uv pip install package-name` (installs to virtual environment)
   - ❌ **Incorrect**: `pip install package-name` (may install to user packages)
   - Always verify installation location with `uv pip list` or `uv pip show package-name`

## Key Technologies (Tool-Based POC)

### Core Framework
- **Letta (Local)**: Agent runtime with persistent memory
- **CopilotKit**: React-based AI chat interface
- **AG-UI**: WebSocket/SSE real-time communication
- **MLflow**: Comprehensive observability and tracking

### Agent Tools
- **Firecrawl**: Web search and scraping for research
- **E2B**: Sandboxed code execution for analysis
- **HelixDB**: Graph database for knowledge storage
- **LLM Planning**: GPT-4/Claude for task decomposition

### Infrastructure
- **FastAPI**: Backend REST API and WebSocket server
- **PostgreSQL**: Primary data persistence
- **Next.js**: Frontend framework with CopilotKit
- **Local Storage**: All agent data stored locally

## Common Commands

```bash
# Virtual Environment (CRITICAL - Always use first)
source .venv/bin/activate && which python

# Local Letta Server (REQUIRED for agents)
source .venv/bin/activate && letta server --port 8283

# MLflow Monitoring (REQUIRED for tracking)
source .venv/bin/activate && mlflow server --host 0.0.0.0 --port 5002

# Backend Development
cd backend && uvicorn main:app --reload --port 8000

# Frontend Development
cd frontend && npm install && npm run dev

# Install Dependencies
source .venv/bin/activate && uv pip install -r backend/requirements.txt

# Letta Agent Management
letta list agents  # List all local agents
letta show <agent_id>  # View agent details
letta delete <agent_id>  # Delete specific agent
letta delete --all  # Clear all agents

# Testing
source .venv/bin/activate && pytest backend/tests/
npm run test --prefix frontend

# Check Service Status
curl http://localhost:8283/health  # Letta
curl http://localhost:8000/docs  # Backend
curl http://localhost:5002  # MLflow
```

## Frontend Design System

ATLAS uses a sophisticated dark theme design with glassmorphism effects and a professional multi-agent dashboard interface.

### Design Aesthetic
- **Theme**: Dark theme with glassmorphism effects and subtle shadows
- **Typography**: Inter font family for modern, clean readability
- **Layout**: Three-panel dashboard (left sidebar, main content, right questions panel)
- **Interactive Elements**: Hover effects, status indicators, progress bars

### Color Palette
```css
Primary Colors:
- Background: #0f172a (Dark slate)
- Primary: #2563eb (Blue)
- Primary Light: #3b82f6 (Light blue)
- Accent: #f59e42 (Orange)

Status Colors:
- Active: #22c55e (Green with glow)
- Processing: #f59e42 (Orange with glow)
- Idle: #94a3b8 (Gray with glow)

Glass Effects:
- Sidebar: rgba(30, 41, 59, 0.8) with blur
- Cards: rgba(51, 65, 85, 0.8) with blur
- Borders: #334155 (Slate)
- Text: #f8fafc (Light)
- Muted: #94a3b8 (Gray)
```

### Application Structure

**Dashboard View**: Project overview with metrics, recent activity, quick actions, file management, suggestions, and analytics. **Tasks Tab**: Project-scoped agent monitoring with hierarchical visualization, dialogue windows, multi-modal support, and real-time AG-UI updates. **Navigation**: Dashboard → Task Execution → Results → Return to Dashboard.

### Agent Visualization
- **Hierarchical Layout**: Global Supervisor → Team Supervisors → Worker Agents
- **Status Indicators**: Colored dots with glow effects (active/processing/idle)
- **Progress Bars**: Gradient progress indicators showing completion percentage
- **Card Hover Effects**: Subtle lift and shadow enhancement on hover

### Reference Files
The original design prototype is preserved in `/frontend/reference-design/`:
- `index.html` - Complete HTML structure and layout
- `style.css` - Full CSS styling with custom properties and glassmorphism
- `app.js` - Vanilla JavaScript interactions and event handlers

**IMPORTANT**: These reference files serve as the design source of truth for the Next.js implementation and should be maintained for consistency. The Next.js components faithfully recreate this design using React and Tailwind CSS.

### Technology Stack
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS with custom dark theme configuration
- **Typography**: Inter font via Google Fonts
- **Icons**: Heroicons for UI elements
- **State**: React hooks for component state (Zustand planned for global state)

### Multi-Modal Content Support
Rich content rendering supporting text (markdown), images (zoom/download), files (preview/download), audio (waveform player), code (syntax highlighting), JSON (collapsible trees), and charts (interactive visualizations). Components: ContentRenderer, TextRenderer, ImageRenderer, FileRenderer, AudioRenderer, CodeRenderer, JSONRenderer, ChartRenderer.

## AG-UI Real-Time Communication System

ATLAS implements a sophisticated real-time communication system using the AG-UI (Agent-Generated User Interface) protocol for seamless frontend-backend interaction.

### Architecture Overview

**Backend Components:**
- **AGUIServer** (`backend/src/agui/server.py`): FastAPI-based WebSocket/SSE server
- **AGUIEvent** (`backend/src/agui/events.py`): Structured event system with 20+ event types
- **AGUIEventHandler** (`backend/src/agui/handlers.py`): Event processing and routing
- **AGUIEventBroadcaster**: Utility for broadcasting events from agent code

**Frontend Components:**
- **AGUIClient** (`frontend/src/lib/agui-client.ts`): TypeScript client for real-time communication
- **Connection Management**: Auto-reconnect, heartbeat, and connection status monitoring
- **Event Handlers**: Type-safe event handling with convenience functions

### Communication Protocols

**WebSocket (Bidirectional)**: Task connection, user input, agent control. **Server-Sent Events (Unidirectional)**: Real-time updates with automatic event processing.

### Event Types Supported

**Task Management:**
- `task_created`, `task_started`, `task_progress`, `task_completed`
- `task_failed`, `task_cancelled`, `task_status_changed`

**Agent Communication:**
- `agent_status_changed`, `agent_dialogue_update`, `agent_message_sent`
- `agent_error`, `agent_interrupted`, `agent_completed`

**Multi-Modal Content:**
- `content_generated`, `content_type_detected`, `file_uploaded`, `file_processed`

**Performance Monitoring:**
- `performance_metrics`, `cost_update`, `token_usage_update`

**User Interaction:**
- `user_input_received`, `user_approval_required`, `user_feedback_received`

### Backend Integration

**Broadcasting**: Agent status changes, dialogue updates, content generation via AGUIEventBroadcaster. **MLflow Integration**: Multi-modal content tracking and dialogue message statistics.

### Frontend Integration

**Event Handling**: Specific event handlers for agent dialogue updates, task progress, and global events. **Convenience Functions**: Type-safe handlers for dialogue updates, agent status changes, and task progress.

### Development and Testing

**Simulation Endpoint**: `/api/dev/simulate-agent-activity` for testing AG-UI with simulated agent activity. **Connection Monitoring**: Real-time connection status tracking with connection type and task ID.

### Deployment Configuration

**Backend Endpoints**: SSE stream, WebSocket connection, broadcast endpoints. **CORS**: Configured for localhost development ports. **Error Handling**: Automatic reconnection with exponential backoff, connection state management, graceful degradation, comprehensive logging.

## Testing Strategy

**Unit Tests**: Individual function/class testing with mocked dependencies (pytest/Jest). **Integration Tests**: Component interactions, API contracts, database operations with Docker containers. **End-to-End Tests**: Full workflow testing with Playwright automation, agent coordination, and output quality verification.

## Code Review Process

Before implementing: discuss approach, review existing patterns, design interface, consider edge cases, plan tests.

## Architecture Decisions

**Backend**: FastAPI (async, OpenAPI, WebSocket), LangGraph (state machine coordination), Letta (persistent memory), Pydantic (type validation). **Frontend**: Next.js 14 (App Router), TypeScript (type safety), shadcn/ui (accessible components), Tailwind CSS (utility-first). **Infrastructure**: Docker Compose, PostgreSQL (ACID compliance), Redis (caching/pub-sub), ChromaDB (vector search), Neo4j (graph relationships).

## Database Design Decisions

### Architecture Principles
1. **Foreign Keys**: Use foreign keys to maintain referential integrity between agent sessions and tasks
2. **Memory Storage**: Hybrid approach - store agent memories in both PostgreSQL (for queries) and ChromaDB (for similarity search)
3. **Naming Convention**: Use snake_case for all database objects
4. **Data Retention**: Keep all execution data for analysis and continuous improvement
5. **Knowledge Graph**: System-level knowledge graph maintains relationships across projects

### Indexing Strategy & Key Metrics
Optimized for the following query patterns and metrics tracking:
- **Primary Indexes**: task_id, agent_id, project_name, timestamp ranges
- **Project Metrics**:
  - Number of messages and tokens per project
  - Average cost per project and per token
  - Model usage distribution and provider breakdown
- **Performance Metrics**:
  - Average time per query
  - Average tokens per prompt/message
  - Task type classification (via LLM analysis)
- **Quality Metrics**:
  - Project summaries (generated via LLM)
  - Cost efficiency trends
  - Model performance comparisons

### Database Roles
- **PostgreSQL**: Transactional data, agent sessions, task management, file metadata
- **Redis**: Real-time caching, pub/sub for agent communication
- **ChromaDB**: Vector embeddings for semantic search and agent memory
- **Neo4j**: Knowledge graph for entity relationships and project connections
- **Local Filesystem**: Multi-modal files (images, audio, video, 3D models) with database references

### File Storage Strategy
**Multi-Modal Content Support**:
- **File Storage**: Local filesystem with structured paths (`/data/files/{project_name}/{file_type}/`)
- **Database References**: File metadata, paths, and checksums stored in PostgreSQL
- **Supported Types**: Images (PNG, JPG, GIF), Audio (MP3, WAV), Video (MP4, AVI), 3D Models (OBJ, STL, PLY)
- **Access Pattern**: Database stores file_path, size, checksum → Application retrieves from filesystem

### Current Risks & Mitigation
1. **Database Connection Complexity**: Multiple database types requiring different connection patterns
   - *Mitigation*: Create unified connection manager with health checks
2. **Virtual Environment Dependencies**: Local service management complexity
   - *Mitigation*: Document all installation steps and create startup scripts
3. **Data Consistency**: Cross-database transactions not possible
   - *Mitigation*: Use application-level consistency checks and rollback procedures
4. **File Storage Scalability**: Local filesystem limitations for large files
   - *Mitigation*: Design file storage interface to easily switch to cloud storage later

## Repository Information

- **GitHub**: https://github.com/CuriosityQuantified/ATLAS
- **Contact**: CuriosityQuantified@gmail.com
- Do not use this when you push to GitHub: 🤖 Generated with [Claude Code](https://claude.ai/code) Co-Authored-By: Claude <noreply@anthropic.com>
