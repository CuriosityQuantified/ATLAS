# Letta Integration for ATLAS

This module integrates Letta (formerly MemGPT) into ATLAS to provide persistent agent memory and an Agent Development Environment (ADE).

## Features

- **Agent Development Environment (ADE)**: Web-based UI for creating and managing Letta agents
- **Chat Interface**: Real-time conversation with agents including message history
- **CLI Tool**: Command-line interface for local IDE integration
- **API Integration**: RESTful API endpoints for agent management
- **Real-time Updates**: AG-UI protocol integration for live agent status

## Architecture

### Backend Components
- `backend/src/letta/` - Core Letta integration
  - `service.py` - LettaService class for agent operations
  - `models.py` - Pydantic models for type safety
  - `__init__.py` - Module exports

- `backend/src/api/letta_endpoints.py` - REST API endpoints

### Frontend Components  
- `frontend/src/app/letta-ade/` - Agent Development Environment page
- `frontend/src/components/letta/` - Reusable Letta components
  - `ChatInterface.tsx` - Real-time chat component

### CLI Tool
- `letta-integration/letta_cli.py` - Command-line interface for local development

## Usage

### Web Interface

1. Start the ATLAS backend server:
   ```bash
   cd backend
   source ../.venv/bin/activate
   uvicorn main:app --reload
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to the Letta ADE:
   - Click on "Letta ADE" in the sidebar
   - Or go directly to http://localhost:3002/letta-ade

### Command Line Interface

The CLI tool allows you to manage agents from your local IDE:

```bash
# Activate virtual environment
source .venv/bin/activate

# List all agents
python letta-integration/letta_cli.py list

# Create a new agent
python letta-integration/letta_cli.py create "MyAgent" --model gpt-4 --persona "You are a helpful coding assistant"

# Chat with an agent
python letta-integration/letta_cli.py chat <agent_id>

# Show conversation history
python letta-integration/letta_cli.py history <agent_id> --limit 50

# Export agent to JSON
python letta-integration/letta_cli.py export <agent_id> my_agent.json

# Delete an agent
python letta-integration/letta_cli.py delete <agent_id>
```

### API Endpoints

The following REST endpoints are available:

- `GET /api/letta/agents` - List all agents
- `POST /api/letta/agents` - Create a new agent
- `GET /api/letta/agents/{agent_id}` - Get agent details
- `PUT /api/letta/agents/{agent_id}` - Update an agent
- `DELETE /api/letta/agents/{agent_id}` - Delete an agent
- `POST /api/letta/agents/{agent_id}/messages` - Send a message
- `GET /api/letta/agents/{agent_id}/conversation` - Get conversation history
- `GET /api/letta/agents/{agent_id}/stream` - SSE stream for real-time updates

## Configuration

Letta requires API keys for the LLM providers. Add these to your `.env` file:

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
# Add other LLM provider keys as needed
```

## Testing

### Test Backend Integration
```bash
source .venv/bin/activate
python letta-integration/test_letta_backend.py
```

### Test CLI Tool
```bash
# Create a test agent
python letta-integration/letta_cli.py create "TestAgent"

# List agents to get the ID
python letta-integration/letta_cli.py list

# Start a chat session
python letta-integration/letta_cli.py chat <agent_id>
```

### Test Frontend
1. Open the ADE in your browser
2. Create a new agent using the "Create Agent" button
3. Select the agent to open the chat interface
4. Send messages and verify responses

## Key Workflows

### 1. Creating Agents via Frontend
- Click "Create Agent" in the ADE
- Fill in agent details (name, model, persona)
- Agent appears in the list immediately
- Select to start chatting

### 2. Creating Agents via IDE
- Use the CLI tool to create agents
- Agents created via CLI appear in the frontend
- Full bidirectional sync between IDE and web

### 3. Conversing with Agents
- Web: Select agent and use chat interface
- CLI: Run `chat` command for interactive session
- All conversations are persisted

## Troubleshooting

### Common Issues

1. **"Letta client initialization failed"**
   - Check that API keys are set in `.env`
   - Verify Letta package is installed: `uv pip install letta`

2. **Agents not appearing in frontend**
   - Ensure backend server is running
   - Check browser console for errors
   - Verify CORS settings in backend

3. **CLI import errors**
   - Make sure virtual environment is activated
   - Check that backend path is correct in CLI script

## Future Enhancements

- [ ] Agent editing functionality
- [ ] Import/export agent configurations
- [ ] Agent templates and presets
- [ ] Memory visualization
- [ ] Multi-agent conversations
- [ ] Agent performance metrics