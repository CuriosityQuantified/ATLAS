## Project Overview

ATLAS (Agentic Task Logic & Analysis System) is a hierarchical multi-agent system designed for modular reasoning and structured content generation. The system decomposes complex tasks into specialized sub-processes managed by autonomous but coordinated agent teams.

Always ask the user questions for code and design choices. 

## Architecture

### Core Components
- **Global Supervisor Agent**: Top-level coordinator that owns the full task and routes responsibilities
- **Four Specialized Teams**:
  - 🕵️‍♂️ Research Team: Information gathering and source aggregation
  - 📊 Analysis Team: Data interpretation and analytical frameworks (SWOT, pros/cons, etc.)
  - ✍️ Writing Team: Content generation with coherence and tone management
  - 📈 Rating/Feedback Team: Quality control and revision suggestions

### Key Architectural Patterns
- **Hierarchical Structure**: Each team has a Supervisor Agent managing multiple Worker Agents
- **Feedback Loops**: Rating outputs flow back to Global Supervisor for potential reassignment
- **Memory System**: Persistent store using vector DB + structured JSON for findings, decisions, and drafts
- **Modular Design**: Each sub-team is reusable and plug-and-play

## Development Status

Ready to begin implementation. Foundation documentation complete.

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
The system will integrate various MCP servers for enhanced tooling:
- Neo4j for knowledge graphs
- GitHub for version control operations
- Firecrawl for web scraping
- Office integration (PowerPoint, Excel)
- Notion, YouTube, and other platform integrations

### Output Formats
- Structured JSON with final_output, evidence_chain, analysis_summary, and ratings
- Mind maps (Freeplane-compatible)
- Neo4j knowledge graphs
- Audio/podcast generation (Mozilla TTS + Podcast Generator)

## Environment Configuration

Required API keys (stored in `.env`):
- `LETTA_API_KEY`
- `ANTHROPIC_API_KEY`
- `TAVILY_API_KEY`
- `GITHUB_API_KEY`
- `FIRECRAWL_API_KEY`
- `GROQ_API_KEY`

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

## Repository Information

- **GitHub**: https://github.com/CuriosityQuantified/ATLAS
- **Contact**: CuriosityQuantified@gmail.com