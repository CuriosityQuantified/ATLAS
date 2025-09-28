"""
Test Suite 1: API Integration Tests
Test FastAPI endpoints from main.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_root_endpoint(test_client):
    """Verify API information."""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert data["service"] == "ATLAS Backend API"
    assert data["status"] == "running"
    assert "features" in data
    assert data["features"]["agui_protocol"] == "enabled"
    assert data["features"]["multi_agent_support"] == "enabled"

    # Check endpoints are listed
    assert "endpoints" in data
    assert "/health" in data["endpoints"]["health"]
    assert "/docs" in data["endpoints"]["api_docs"]


def test_health_check(test_client):
    """Check service status."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "services" in data
    assert data["services"]["agui_server"] == "running"


def test_create_task(test_client):
    """Create ATLAS task via API - Scenario 1."""
    # First, ensure app.state has the agui_broadcaster attribute
    from main import app
    if not hasattr(app.state, 'agui_broadcaster'):
        app.state.agui_broadcaster = MagicMock()

    # Mock the AG-UI broadcaster to avoid actual WebSocket connections
    with patch.object(app.state, 'agui_broadcaster') as mock_broadcaster:
        mock_broadcaster.broadcast_task_progress = MagicMock(return_value=None)

        # Test data for creating a task
        task_data = {
            "task_type": "research",
            "description": "Analyze remote work trends",
            "priority": "medium"
        }

        # Make POST request to create task
        response = test_client.post("/api/tasks", json=task_data)

        # Verify response
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        assert response.status_code == 200
        data = response.json()

        # Check required fields in response
        assert "task_id" in data
        assert data["status"] == "created"
        assert "message" in data
        assert "websocket_url" in data
        assert "sse_url" in data

        # Verify WebSocket URL format
        task_id = data["task_id"]
        assert data["websocket_url"] == f"/api/agui/ws/{task_id}"
        assert data["sse_url"] == f"/api/agui/stream/{task_id}"


def test_get_task_status(test_client):
    """Retrieve task status."""
    # First create a task to get a task_id
    with patch('main.app.state.agui_broadcaster'):
        create_response = test_client.post("/api/tasks", json={"query": "test"})
        task_id = create_response.json()["task_id"]

    # Now get the task status
    response = test_client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    data = response.json()

    # Check status fields
    assert data["task_id"] == task_id
    assert "status" in data
    assert "progress" in data
    assert "current_phase" in data
    assert "agents_active" in data


def test_list_agents(test_client):
    """List available agents."""
    response = test_client.get("/api/agents")

    assert response.status_code == 200
    data = response.json()

    # Check agent hierarchy
    assert "global_supervisor" in data
    assert data["global_supervisor"]["type"] == "supervisor"
    assert data["global_supervisor"]["status"] == "ready"

    # Check team structure
    assert "research_team" in data
    assert "analysis_team" in data
    assert "writing_team" in data
    assert "rating_team" in data

    # Verify research team structure
    research_team = data["research_team"]
    assert "supervisor" in research_team
    assert "workers" in research_team
    assert "web_researcher" in research_team["workers"]


def test_simulate_agent_activity(test_client):
    """Test AG-UI simulation."""
    with patch('main.app.state.agui_broadcaster') as mock_broadcaster:
        # Setup mock broadcaster methods
        mock_broadcaster.broadcast_agent_status = MagicMock(return_value=None)
        mock_broadcaster.broadcast_dialogue_update = MagicMock(return_value=None)
        mock_broadcaster.broadcast_content_generated = MagicMock(return_value=None)

        simulation_data = {
            "task_id": "test_task_123",
            "agent_id": "test_agent_456"
        }

        response = test_client.post("/api/dev/simulate-agent-activity", json=simulation_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "message" in data
        assert data["events_sent"] == 3

        # Verify broadcaster methods were called
        mock_broadcaster.broadcast_agent_status.assert_called_once()
        mock_broadcaster.broadcast_dialogue_update.assert_called_once()
        mock_broadcaster.broadcast_content_generated.assert_called_once()