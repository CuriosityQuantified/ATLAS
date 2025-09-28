"""
Shared test fixtures and configuration for ATLAS backend tests
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import shutil

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    from main import app

    # Create test client
    client = TestClient(app)
    return client

@pytest.fixture
async def async_test_client():
    """Create async FastAPI test client for async endpoints."""
    from httpx import AsyncClient
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_letta_server():
    """Mock Letta server for testing without actual server running."""
    with patch('src.agents.letta_config.check_server_health') as mock_health:
        mock_health.return_value = True

        # Mock the Letta client
        with patch('letta_client.client.Letta') as mock_letta:
            # Create mock client instance
            mock_client = MagicMock()
            mock_letta.return_value = mock_client

            # Mock agent operations
            mock_agent = MagicMock()
            mock_agent.id = "test_agent_123"
            mock_agent.name = "test_agent"
            mock_agent.created_at = "2024-01-01T00:00:00Z"

            # Mock agent creation
            mock_client.agents.create.return_value = mock_agent
            mock_client.agents.get.return_value = mock_agent
            mock_client.agents.list.return_value = [mock_agent]
            mock_client.agents.delete.return_value = None

            # Mock message sending
            mock_response = MagicMock()
            mock_response.messages = [
                {"content": "Test response", "role": "assistant"}
            ]
            mock_client.agents.messages.send.return_value = mock_response

            yield mock_client

@pytest.fixture
def test_session_dir():
    """Create temporary session directory for file operations."""
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="atlas_test_session_")
    session_dir = Path(temp_dir) / "outputs" / "test_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Mock the session directory path
    with patch('src.tools.file_tool.get_session_directory') as mock_get_dir:
        mock_get_dir.return_value = str(session_dir)
        yield session_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_llm():
    """Mock LLM for planning tool tests."""
    with patch('src.tools.planning_tool.call_llm') as mock_call_llm:
        # Mock planning response
        mock_call_llm.return_value = {
            "plan": [
                {
                    "step_id": "step_1",
                    "description": "Research the topic",
                    "task_type": "research",
                    "dependencies": [],
                    "estimated_duration": "30 minutes"
                },
                {
                    "step_id": "step_2",
                    "description": "Analyze findings",
                    "task_type": "analysis",
                    "dependencies": ["step_1"],
                    "estimated_duration": "45 minutes"
                }
            ]
        }
        yield mock_call_llm

@pytest.fixture
def captured_tool_calls():
    """Capture tool calls for verification."""
    calls = []

    def capture_call(tool_name, *args, **kwargs):
        calls.append({
            "tool": tool_name,
            "args": args,
            "kwargs": kwargs
        })
        return {"status": "success", "task_id": f"test_{tool_name}"}

    return calls, capture_call

@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset any global state between tests."""
    # Reset planning stores
    from src.tools import planning_tool
    if hasattr(planning_tool, '_plan_stores'):
        planning_tool._plan_stores.clear()

    # Reset todo stores
    from src.tools import todo_tool
    if hasattr(todo_tool, '_todo_stores'):
        todo_tool._todo_stores.clear()

    # Reset file tool session
    from src.tools import file_tool
    if hasattr(file_tool, '_session_directory'):
        file_tool._session_directory = None

    yield

    # Cleanup after test
    # (Same cleanup as above)