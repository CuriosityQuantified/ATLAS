#!/bin/bash

# ============================================================================
# ATLAS - Start Local Letta Server with Web ADE Support
# ============================================================================
# This script starts the local Letta server for development with full
# visibility through the Web-based Agent Development Environment (ADE)
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
VENV_PATH="/Users/nicholaspate/Documents/01_Active/ATLAS/.venv"
PROJECT_ROOT="/Users/nicholaspate/Documents/01_Active/ATLAS"
LETTA_PORT=8283
LETTA_CONFIG_DIR="$HOME/.letta"

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}     ATLAS - Letta Server with Web ADE Integration${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}✗ Virtual environment not found at: $VENV_PATH${NC}"
    echo -e "${YELLOW}Please create it first with: uv venv${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}→ Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Verify Letta is installed
LETTA_CMD="$VENV_PATH/bin/letta"
if [ ! -f "$LETTA_CMD" ]; then
    echo -e "${RED}✗ Letta is not installed!${NC}"
    echo -e "${YELLOW}Install it with: uv pip install letta sqlite-vec${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Letta found: $LETTA_CMD${NC}"

# Check if Letta is configured
if [ ! -d "$LETTA_CONFIG_DIR" ]; then
    echo -e "${YELLOW}⚠ First time setup detected${NC}"
    echo -e "${BLUE}→ Running Letta configuration...${NC}"
    echo ""
    echo -e "${CYAN}Please select the following options:${NC}"
    echo "  1. Storage backend: ${GREEN}local${NC}"
    echo "  2. Database: ${GREEN}sqlite${NC}"
    echo "  3. Use default settings for other options"
    echo ""
    $LETTA_CMD configure
    echo -e "${GREEN}✓ Letta configuration complete${NC}"
fi

# Check if port is already in use
if lsof -Pi :$LETTA_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port $LETTA_PORT is already in use${NC}"
    echo -e "${BLUE}Checking if it's a Letta server...${NC}"

    if curl -s http://localhost:$LETTA_PORT/v1/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Letta server is already running!${NC}"
        echo ""
    else
        echo -e "${RED}✗ Another process is using port $LETTA_PORT${NC}"
        echo -e "${YELLOW}Please stop it first or use a different port${NC}"
        exit 1
    fi
else
    # Start Letta server
    echo ""
    echo -e "${BLUE}→ Starting Letta server on port $LETTA_PORT...${NC}"
    echo ""
fi

# Display connection information
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}     Letta Server Ready for Development${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "${CYAN}📡 Server Endpoints:${NC}"
echo -e "   API: ${GREEN}http://localhost:$LETTA_PORT/v1${NC}"
echo -e "   Health: ${GREEN}http://localhost:$LETTA_PORT/v1/health${NC}"
echo ""
echo -e "${CYAN}🌐 Web ADE Connection Instructions:${NC}"
echo -e "   1. Open browser: ${BLUE}https://app.letta.com${NC}"
echo -e "   2. Sign in with GitHub, Google, or email"
echo -e "   3. Click '${YELLOW}Self-hosted${NC}' tab in left panel"
echo -e "   4. Enter server URL: ${GREEN}http://localhost:$LETTA_PORT${NC}"
echo -e "   5. Click '${YELLOW}Connect${NC}' to link ADE to your local server"
echo ""
echo -e "${CYAN}🛠️  Available ADE Features:${NC}"
echo -e "   ${GREEN}•${NC} Agent Simulator - Interactive testing & monitoring"
echo -e "   ${GREEN}•${NC} Memory Inspector - View/edit agent memory blocks"
echo -e "   ${GREEN}•${NC} Tool Editor - Write & test Python tools in browser"
echo -e "   ${GREEN}•${NC} Context Window - See exactly what the LLM sees"
echo -e "   ${GREEN}•${NC} System Instructions - Configure agents without code"
echo ""
echo -e "${CYAN}📝 Quick Test:${NC}"
echo -e "   Run: ${YELLOW}python $PROJECT_ROOT/backend/src/agents/letta_config.py${NC}"
echo -e "   This will validate your environment setup"
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the server (if not already running)
if ! curl -s http://localhost:$LETTA_PORT/v1/health >/dev/null 2>&1; then
    # Start server with proper port and ADE support
    $LETTA_CMD server --port $LETTA_PORT --ade
else
    echo -e "${CYAN}Server already running. Monitoring logs...${NC}"
    echo -e "${YELLOW}You can start working with the Web ADE now!${NC}"
    # Keep script running to show it's active
    tail -f /dev/null
fi