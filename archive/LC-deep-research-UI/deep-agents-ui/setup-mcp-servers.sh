#!/bin/bash

# Setup MCP Servers for Claude Code
echo "Setting up MCP servers for Claude Code..."

# Add GitHub MCP server
echo "Adding GitHub server..."
claude mcp add github npx -- -y @modelcontextprotocol/server-github
echo "✅ GitHub server added"

# Add Memgraph server (for your knowledge graph)
echo "Adding Memgraph server..."
claude mcp add mcp-memgraph /Users/nicholaspate/.local/bin/uv -- run --with mcp-memgraph --python 3.13 mcp-memgraph
echo "✅ Memgraph server added"

# Add Tavily search server  
echo "Adding Tavily search server..."
claude mcp add tavily-mcp npx -- -y @smithery/cli@latest run @tavily-ai/tavily-mcp --key 69575234-6246-4faa-bdc7-0bcc0713e2b5 --profile crazy-flea-UGGFtX
echo "✅ Tavily server added"

# Add Task Manager
echo "Adding Task Manager server..."
claude mcp add mcp-taskmanager npx -- -y @smithery/cli@latest run @kazuph/mcp-taskmanager --key 69575234-6246-4faa-bdc7-0bcc0713e2b5
echo "✅ Task Manager server added"

# List all configured servers
echo ""
echo "Configured MCP servers:"
claude mcp list

echo ""
echo "Setup complete! You can now use these MCP servers in Claude Code."
echo ""
echo "Note: For the GitHub server, set your token with:"
echo "export GITHUB_PERSONAL_ACCESS_TOKEN='your-token-here'"