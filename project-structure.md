# ATLAS Project Structure

## Monorepo Organization

```
ATLAS/
├── backend/                      # Python FastAPI backend
│   ├── src/
│   │   ├── atlas/               # Main application package
│   │   │   ├── __init__.py
│   │   │   ├── main.py          # FastAPI app entry point
│   │   │   ├── config.py        # Configuration management
│   │   │   ├── agents/          # Agent implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py      # Base agent classes
│   │   │   │   ├── supervisor.py # Supervisor agent base
│   │   │   │   ├── worker.py    # Worker agent base
│   │   │   │   └── global_supervisor.py
│   │   │   ├── teams/           # Team implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── research/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── supervisor.py
│   │   │   │   │   └── workers.py
│   │   │   │   ├── analysis/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── supervisor.py
│   │   │   │   │   └── workers.py
│   │   │   │   ├── writing/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── supervisor.py
│   │   │   │   │   └── workers.py
│   │   │   │   └── rating/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── supervisor.py
│   │   │   │       └── workers.py
│   │   │   ├── memory/          # Memory system
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manager.py   # Memory manager
│   │   │   │   ├── shared.py    # Shared memory implementation
│   │   │   │   ├── isolated.py  # Isolated memory implementation
│   │   │   │   └── chromadb_client.py
│   │   │   ├── tools/           # MCP servers and tools
│   │   │   │   ├── __init__.py
│   │   │   │   ├── web_search.py
│   │   │   │   ├── document_loader.py
│   │   │   │   ├── neo4j_client.py
│   │   │   │   └── mcp_integrations.py
│   │   │   ├── api/             # API routes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tasks.py     # Task endpoints
│   │   │   │   ├── agents.py    # Agent management
│   │   │   │   ├── memory.py    # Memory access
│   │   │   │   └── websocket.py # Real-time updates
│   │   │   ├── models/          # Data models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── task.py
│   │   │   │   ├── agent.py
│   │   │   │   └── output.py
│   │   │   └── utils/           # Utilities
│   │   │       ├── __init__.py
│   │   │       ├── logging.py
│   │   │       └── prompts.py
│   │   └── tests/               # Test suite
│   │       ├── unit/
│   │       ├── integration/
│   │       └── e2e/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/                     # React/Next.js frontend
│   ├── src/
│   │   ├── app/                 # Next.js app router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── tasks/
│   │   │   ├── agents/
│   │   │   └── api/
│   │   ├── components/          # React components
│   │   │   ├── agents/
│   │   │   ├── tasks/
│   │   │   ├── memory/
│   │   │   └── ui/
│   │   ├── lib/                 # Utilities
│   │   │   ├── api.ts
│   │   │   ├── websocket.ts
│   │   │   └── types.ts
│   │   └── styles/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   └── Dockerfile
│
├── shared/                       # Shared configurations
│   ├── types/                   # TypeScript types
│   ├── constants/               # Shared constants
│   └── schemas/                 # JSON schemas
│
├── scripts/                      # Development scripts
│   ├── setup.sh
│   ├── test.sh
│   └── deploy.sh
│
├── docs/                        # Documentation
│   ├── architecture/
│   ├── api/
│   └── guides/
│
├── docker-compose.yml           # Local development
├── docker-compose.prod.yml      # Production setup
├── .env.example
├── .gitignore
├── README.md
└── CLAUDE.md
```

## Key Design Decisions

### Backend Structure
- **`atlas/`**: Main application package containing all business logic
- **`agents/`**: Base classes for all agent types (supervisor, worker)
- **`teams/`**: Modular team implementations, each team is self-contained
- **`memory/`**: Centralized memory management with clear separation of shared vs isolated
- **`tools/`**: All external integrations (MCP servers, APIs, etc.)
- **`api/`**: FastAPI routes organized by domain

### Frontend Structure
- **App Router**: Using Next.js 14+ app router for modern React patterns
- **Component Organization**: Grouped by feature (agents, tasks, memory)
- **Type Safety**: Shared types between frontend and backend

### Shared Resources
- **Types**: TypeScript definitions shared between frontend/backend
- **Schemas**: JSON schemas for validation and documentation
- **Constants**: Shared configuration values

### Development Experience
- **Docker Compose**: Separate configs for dev and prod
- **Scripts**: Automation for common tasks
- **Testing**: Organized by test type (unit, integration, e2e)