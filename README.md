# ATLAS - Agentic Task Logic & Analysis System

A hierarchical multi-agent system designed for modular reasoning and structured content generation. ATLAS decomposes complex tasks into specialized sub-processes managed by autonomous but coordinated agent teams.

## 🏗️ Architecture

### Core Components
- **Global Supervisor Agent**: Top-level coordinator that owns the full task and routes responsibilities
- **Four Specialized Teams**:
  - 🕵️‍♂️ **Research Team**: Information gathering and source aggregation
  - 📊 **Analysis Team**: Data interpretation and analytical frameworks (SWOT, pros/cons, etc.)
  - ✍️ **Writing Team**: Content generation with coherence and tone management
  - 📈 **Rating/Feedback Team**: Quality control and revision suggestions

## 📁 Project Structure

```
ATLAS/
├── docs/                     # Documentation
├── infrastructure/           # Docker & configs
├── mlflow/                   # Monitoring & observability
├── frontend/                 # Next.js UI
├── backend/                  # FastAPI + agents
├── shared/                   # Common configs & types
└── scripts/                  # Build & deployment scripts
```

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   npm run setup
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Update .env with your API keys
   ```

3. **Start Services**
   ```bash
   npm run docker:up
   npm run dev
   ```

4. **Access Applications**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MLflow UI: http://localhost:5000

## 🛠️ Development Plan

### Step 1: Docker & MLflow3 Setup ✅
- Containerized infrastructure with monitoring
- PostgreSQL, Redis, ChromaDB, Neo4j, MinIO
- MLflow 3.0 for multi-agent observability

### Step 2: Frontend with Endpoints
- Next.js dashboard with real-time updates
- AG-UI protocol for agent communication
- Interactive workflow visualization

### Step 3: AG-UI Backend Configuration
- FastAPI server with WebSocket/SSE support
- Event broadcasting system
- Frontend-backend communication bridge

### Step 4: LangGraph & Letta Agents
- Multi-agent orchestration with LangGraph
- Persistent memory with Letta
- Tool call coordination patterns

## 🔧 Available Scripts

```bash
npm run dev          # Start development servers
npm run build        # Build all services
npm run test         # Run all tests
npm run docker:up    # Start Docker services
npm run docker:down  # Stop Docker services
npm run health       # Check service health
```

## 📚 Documentation

- [Development Plan](docs/plan.md)
- [MLflow3 Guide](docs/guides/mlflow3-guide.md)
- [AG-UI Guide](docs/guides/ag-ui-guide.md)
- [LangGraph Guide](docs/guides/langgraph-guide.md)
- [Letta Integration](docs/guides/letta-comprehensive-guide.md)

## 🌐 Deployment

**Development**: Docker Compose (local)
**Production**: Kubernetes (AWS EKS, Google GKE, or Azure AKS)

Estimated costs:
- Development: $300-600/month
- Production: $800-2500/month

## 🤝 Contributing

1. Follow the 4-step development sequence
2. Maintain DRY, modular, readable code
3. Test changes thoroughly
4. Update documentation

## 📄 License

MIT License - see LICENSE file for details

---

**Contact**: CuriosityQuantified@gmail.com  
**Repository**: https://github.com/CuriosityQuantified/ATLAS