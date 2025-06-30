# ATLAS Development Plan: Comprehensive Build Strategy

## Overview

ATLAS development follows a structured implementation sequence prioritizing infrastructure and frontend-backend communication before multi-agent orchestration. The approach ensures proper monitoring, user interface, and communication protocols are established before building the core agent system.

## Implementation Steps

### Step 1: Docker & MLflow3 Monitoring Setup

Set up the complete containerized infrastructure with comprehensive monitoring and observability.

#### 1.1 Docker Compose Infrastructure

```yaml
# docker-compose.yml
version: '3.8'

services:
  # MLflow3 Tracking Server
  mlflow-server:
    image: python:3.11-slim
    container_name: atlas-mlflow-server
    command: >
      bash -c "
        pip install mlflow[extras]==3.0.0 psycopg2-binary &&
        mlflow server
        --backend-store-uri postgresql://mlflow:mlflow_password@postgres:5432/mlflow
        --default-artifact-root s3://mlflow-artifacts
        --host 0.0.0.0
        --port 5000
        --serve-artifacts
      "
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_TRACKING_URI=http://localhost:5000
      - MLFLOW_S3_ENDPOINT_URL=http://minio:9000
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin
    depends_on:
      - postgres
      - minio
    networks:
      - atlas-network

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: atlas-postgres
    environment:
      POSTGRES_DB: mlflow
      POSTGRES_USER: mlflow
      POSTGRES_PASSWORD: mlflow_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - atlas-network

  # MinIO for Artifact Storage
  minio:
    image: minio/minio:latest
    container_name: atlas-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - atlas-network

  # Additional services configured in detailed guides...

volumes:
  postgres_data:
  minio_data:

networks:
  atlas-network:
    driver: bridge
```

#### 1.2 MLflow3 Monitoring Features

- **Multi-Agent Tracking**: Monitor individual agent performance and coordination
- **Real-time Dashboards**: Live performance metrics and quality scores
- **Cost Tracking**: API usage and resource consumption monitoring
- **Error Analysis**: Comprehensive error tracking and recovery patterns
- **Experiment Management**: Version control for prompts, agents, and workflows

### Step 2: Frontend Setup with Endpoints

Build the user interface with real-time communication endpoints for updating the UI.

#### 2.1 Frontend Architecture

```typescript
// Frontend stack configuration
const frontendStack = {
  framework: "Next.js 14+ with App Router",
  ui_library: "shadcn/ui with Tailwind CSS",
  state_management: "Zustand for client state",
  real_time: "AG-UI Protocol for agent communication",
  api_client: "tRPC for type-safe API calls",
  deployment: "Vercel or containerized"
};
```

#### 2.2 API Endpoints Structure

```typescript
// API endpoint definitions for UI updates
interface ATLASAPIEndpoints {
  // Task Management
  "/api/tasks/create": "POST - Create new ATLAS task",
  "/api/tasks/[id]/status": "GET - Get task status",
  "/api/tasks/[id]/cancel": "POST - Cancel running task",
  
  // Real-time Updates
  "/api/stream/[taskId]": "SSE - Server-sent events for task updates",
  "/api/websocket": "WS - WebSocket connection for bidirectional communication",
  
  // Agent Management
  "/api/agents/status": "GET - Get all active agents",
  "/api/agents/[id]/interrupt": "POST - Interrupt specific agent",
  
  // Results & Outputs
  "/api/results/[taskId]": "GET - Retrieve task results",
  "/api/results/[taskId]/export": "POST - Export results in various formats",
  
  // User Interaction
  "/api/feedback/[taskId]": "POST - Submit user feedback",
  "/api/approval/[taskId]": "POST - Human approval for quality gates"
}
```

#### 2.3 Frontend Components

```typescript
// Core UI components for ATLAS
const uiComponents = {
  TaskCreator: "Modal for creating new analysis tasks",
  AgentDashboard: "Real-time view of all active agents",
  WorkflowVisualizer: "Interactive workflow state visualization",
  ResultsViewer: "Display analysis results with export options",
  ChatInterface: "Conversational interface with agents",
  QualityMonitor: "Real-time quality scores and metrics",
  CostTracker: "Budget and resource usage monitoring"
};
```

### Step 3: AG-UI Backend Configuration

Configure the backend to enable seamless frontend-backend communication through the AG-UI protocol.

#### 3.1 AG-UI Server Setup

```python
# Backend AG-UI configuration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_server import AGUIManager, AGUIEventType

app = FastAPI(title="ATLAS AG-UI Server")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AG-UI manager
agui_manager = AGUIManager()

# AG-UI event streaming endpoint
@app.get("/api/stream/{task_id}")
async def stream_task_events(task_id: str):
    """Stream real-time task events to frontend"""
    return StreamingResponse(
        agui_manager.get_event_stream(task_id),
        media_type="text/event-stream"
    )
```

#### 3.2 Event Broadcasting System

```python
class ATLASEventBroadcaster:
    """Broadcasts ATLAS events through AG-UI protocol"""
    
    async def broadcast_agent_status(self, task_id: str, agent_id: str, status: str):
        """Broadcast agent status changes"""
        await agui_manager.broadcast_event(
            task_id=task_id,
            event_type=AGUIEventType.AGENT_STATUS,
            data={
                "agent_id": agent_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def broadcast_task_progress(self, task_id: str, progress: float, message: str):
        """Broadcast task progress updates"""
        await agui_manager.broadcast_event(
            task_id=task_id,
            event_type=AGUIEventType.TASK_PROGRESS,
            data={
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        )
```

#### 3.3 Backend-Frontend Communication Flow

1. **Frontend initiates task** → POST /api/tasks/create
2. **Backend creates task** → Returns task_id
3. **Frontend connects to SSE** → GET /api/stream/{task_id}
4. **Backend broadcasts events** → Through AG-UI protocol
5. **Frontend updates UI** → Real-time visualization
6. **User provides input** → POST through WebSocket
7. **Backend processes input** → Updates agent behavior
8. **Task completes** → Final results available

### Step 4: Backend Configuration - LangGraph & Letta Agents

Build the core multi-agent orchestration system using LangGraph workflows and Letta memory management.

#### 4.1 LangGraph Workflow Setup

```python
from langgraph import StateGraph, START, END
from atlas_state import ATLASState

class ATLASWorkflow:
    """Main ATLAS workflow using LangGraph"""
    
    def __init__(self):
        self.graph = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(ATLASState)
        
        # Add nodes
        workflow.add_node("global_supervisor", self.global_supervisor_node)
        workflow.add_node("research_team", self.research_team_node)
        workflow.add_node("analysis_team", self.analysis_team_node)
        workflow.add_node("writing_team", self.writing_team_node)
        workflow.add_node("rating_team", self.rating_team_node)
        
        # Define routing
        workflow.add_edge(START, "global_supervisor")
        workflow.add_conditional_edges(
            "global_supervisor",
            self.route_from_supervisor,
            {
                "research": "research_team",
                "analysis": "analysis_team",
                "writing": "writing_team",
                "rating": "rating_team",
                "end": END
            }
        )
        
        return workflow.compile()
```

#### 4.2 Letta Agent Integration

```python
from letta import LettaClient

class ATLASAgentManager:
    """Manages Letta agents with persistent memory"""
    
    def __init__(self):
        self.letta_client = LettaClient()
        
    async def create_agent_for_task(
        self,
        agent_type: str,
        task_id: str,
        persona_config: Dict
    ) -> str:
        """Create fresh agent with long-term memory access"""
        
        # Create agent with relevant memories
        agent = await self.letta_client.create_agent(
            agent_id=f"{agent_type}_{task_id}",
            persona=persona_config['persona'],
            tools=persona_config['tools']
        )
        
        return agent.id
```

## Development Timeline

### Week 1: Infrastructure Setup
- **Day 1-2**: Docker environment and MLflow3 setup
- **Day 3-4**: Database initialization (PostgreSQL, Redis, ChromaDB, Neo4j)
- **Day 5**: MLflow3 integration testing and dashboard configuration

### Week 2: Frontend Development
- **Day 1-2**: Next.js project setup with TypeScript
- **Day 3-4**: Core UI components and AG-UI client integration
- **Day 5**: API endpoints and real-time streaming implementation

### Week 3: Backend Communication
- **Day 1-2**: FastAPI server with AG-UI protocol
- **Day 3-4**: Event broadcasting and WebSocket setup
- **Day 5**: Frontend-backend integration testing

### Week 4: Multi-Agent System
- **Day 1-2**: LangGraph workflow implementation
- **Day 3-4**: Letta agent creation and memory integration
- **Day 5**: Agent coordination and tool integration

### Week 5-8: Advanced Features
- Tool ecosystem and MCP servers
- Enhanced memory system
- Sophisticated agent prompts
- Quality assurance and production features

## Success Criteria

1. **Infrastructure**: All Docker services running with <1s latency
2. **Frontend**: Real-time updates with <100ms UI response time
3. **Communication**: Reliable AG-UI streaming with automatic reconnection
4. **Agents**: Successful multi-agent task completion with quality score >4.0

## Production Deployment Strategy

### Phase 1: Local Development (Docker Compose)
- Complete Step 1-4 using local Docker environment
- Validate all components and integrations
- Optimize performance and resource usage

### Phase 2: Cloud Migration (Managed Kubernetes)
**Recommended Platform:** AWS EKS, Google GKE, or Azure AKS

**Migration Benefits:**
- Auto-scaling capabilities (HPA + VPA + KEDA)
- Cost optimization with spot instances (up to 90% savings)
- Production monitoring with OpenTelemetry + Prometheus + Grafana
- Service mesh for advanced inter-agent communication
- CI/CD with GitOps deployment (ArgoCD)

**Estimated Costs:**
- Development: $300-600/month
- Production: $800-2500/month

### Phase 3: Multi-Cloud Production
- Primary: Chosen cloud provider
- Backup: Different availability zones
- Disaster recovery and scaling strategies

## Current Status & Progress

### Step 1: Docker & MLflow3 Setup ✅ COMPLETED

**Status:** Successfully completed MLflow3 monitoring setup using virtual environment approach after Docker networking challenges.

**Key Achievements:**
- ✅ MLflow 3.0 server running reliably on port 5002
- ✅ Virtual environment setup documented and working
- ✅ Cost calculator utility implemented (`backend/src/utils/cost_calculator.py`)
- ✅ MLflow tracking implementation (`backend/src/mlflow/tracking.py`)
- ✅ Comprehensive documentation created
- ✅ Docker debugging analysis completed
- ✅ Network testing utilities established

**Technical Decisions:**
- **Virtual Environment over Docker**: Chose virtual environment for development after Docker networking issues
- **Port 5002**: MLflow UI accessible at http://localhost:5002
- **Simplified Dependencies**: Streamlined requirements.txt to essential MLflow components
- **Background Process Management**: Using nohup for persistent MLflow server operation

**Documentation Created:**
- `docs/guides/mlflow-virtual-environment-setup.md` - Working setup guide
- `docs/guides/mlflow-docker-debugging.md` - Docker troubleshooting analysis
- `scripts/dev/test-mlflow-networking.py` - Network connectivity testing
- `scripts/dev/verify-mlflow.py` - Full MLflow verification script

### Current Phase: Step 2 - Frontend with Endpoints

**Next Priority Tasks:**

#### 2.1 Next.js Frontend Setup
```bash
# Create Next.js project with TypeScript
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app
```

#### 2.2 shadcn/ui Component Library
```bash
# Install shadcn/ui components
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input label textarea
```

#### 2.3 API Client Setup
```bash
# Install API client dependencies
npm install @tanstack/react-query axios
npm install -D @types/node
```

#### 2.4 Real-time Communication
```bash
# Install SSE and WebSocket support
npm install eventsource-parser
```

**Implementation Order:**
1. **Frontend Project Structure** - Next.js 14 with App Router ✅
2. **Task Execution Interface** - Live agent monitoring during analysis ✅
3. **Tasks Tab Restructuring** - Convert current interface to project-scoped task monitoring
4. **Agent Dialogue Windows** - Multi-modal input/output display per agent
5. **AG-UI Integration** - Real-time dialogue streaming and updates
6. **Dashboard Homepage** - Project overview, metrics, and file management
7. **API Integration** - REST endpoints and error handling
8. **Advanced Analytics** - Performance metrics and AI suggestions

### Success Metrics

**Step 1 Achievements:** ✅
- MLflow server 99.9% uptime during development
- Cost tracking accuracy for all major LLM providers
- Comprehensive documentation enabling reliable reproduction
- Network testing utilities for troubleshooting

**Step 2 Targets:**
- Frontend loads in <2 seconds
- Real-time updates with <100ms latency
- Responsive design across desktop/tablet/mobile
- Type-safe API integration with proper error handling

## Recommended Next Actions

### Immediate (This Week)
1. **Create Frontend Project** - Set up Next.js with TypeScript and shadcn/ui
2. **Build Dashboard Layout** - Main interface with navigation and task overview
3. **Implement API Client** - Type-safe REST API communication
4. **Add Real-time Updates** - Server-sent events for task progress

### Short-term (Next 2 Weeks)
1. **AG-UI Protocol Implementation** - Backend WebSocket/SSE server
2. **Agent Status Visualization** - Real-time agent activity display
3. **Task Management Interface** - Create, monitor, and control tasks
4. **Results Display System** - Formatted output with export options

### Medium-term (Next Month)
1. **LangGraph Integration** - Multi-agent workflow orchestration
2. **Letta Memory System** - Persistent agent memory management
3. **Tool Ecosystem** - MCP server integrations
4. **Quality Assurance** - Automated testing and validation

The foundation is now solid with reliable MLflow monitoring. The next phase focuses on creating the user interface that will enable efficient interaction with the upcoming multi-agent system.
