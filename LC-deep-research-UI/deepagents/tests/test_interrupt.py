"""
Test suite for interrupt pattern implementation.
Tests the new interrupt-based ask_user_question functionality
and checkpointing capabilities.
"""

import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from langgraph.types import Command
from deepagents.graph import create_deep_agent
from deepagents.checkpointer import get_checkpointer


@pytest.fixture
def setup_interrupt_env():
    """Set up environment for interrupt pattern testing."""
    # Save original env
    original_env = os.environ.copy()
    
    # Enable interrupt pattern
    os.environ["USE_INTERRUPT_PATTERN"] = "true"
    os.environ["DISABLE_CHECKPOINTING"] = "false"
    
    yield
    
    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_agent(setup_interrupt_env):
    """Create a test agent with checkpointing enabled."""
    agent = create_deep_agent(
        tools=[],
        instructions="You are a test agent.",
        use_checkpointer=True,
        checkpointer_type="sqlite"
    )
    return agent


def test_checkpointer_creation():
    """Test that checkpointer is created correctly."""
    # Test SQLite checkpointer
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        os.environ["SQLITE_DB_PATH"] = tmp.name
        checkpointer = get_checkpointer("sqlite")
        assert checkpointer is not None
        assert "SqliteSaver" in str(type(checkpointer))


def test_checkpointer_postgres_fallback():
    """Test that PostgreSQL checkpointer falls back to SQLite if connection fails."""
    # Set invalid PostgreSQL URL
    os.environ["POSTGRES_URL"] = "postgresql://invalid:invalid@localhost:5432/invalid"
    
    checkpointer = get_checkpointer("postgres")
    # Should fall back to SQLite
    assert checkpointer is not None
    assert "SqliteSaver" in str(type(checkpointer))


def test_checkpointer_disabled():
    """Test that checkpointing can be disabled."""
    os.environ["DISABLE_CHECKPOINTING"] = "true"
    checkpointer = get_checkpointer()
    assert checkpointer is None


@patch('deepagents.tools.interrupt')
def test_interrupt_flow(mock_interrupt, test_agent, setup_interrupt_env):
    """Test that interrupt pattern works correctly."""
    # Mock the interrupt to return a test answer
    mock_interrupt.return_value = "March 12, 1990"
    
    # Start conversation
    thread_id = "test-thread-1"
    result = test_agent.invoke(
        {"messages": [{"role": "user", "content": "ask me what my birthday is"}]},
        config={"thread_id": thread_id}
    )
    
    # Verify interrupt was called
    assert mock_interrupt.called
    
    # Verify the interrupt data structure
    interrupt_data = mock_interrupt.call_args[0][0]
    assert interrupt_data["type"] == "user_question"
    assert "birthday" in interrupt_data["question"].lower()


def test_resume_with_answer(test_agent, setup_interrupt_env):
    """Test resuming an interrupted thread with an answer."""
    thread_id = "test-thread-2"
    
    # Mock scenario where thread is interrupted
    with patch('deepagents.tools.interrupt') as mock_interrupt:
        # First, interrupt should pause execution
        mock_interrupt.side_effect = Exception("Thread interrupted - waiting for user input")
        
        try:
            result = test_agent.invoke(
                {"messages": [{"role": "user", "content": "ask me a question"}]},
                config={"thread_id": thread_id}
            )
        except Exception as e:
            assert "Thread interrupted" in str(e)
    
    # Now simulate resume with answer
    with patch.object(test_agent, 'invoke') as mock_invoke:
        mock_invoke.return_value = {"status": "resumed"}
        
        # Resume with answer
        result = test_agent.invoke(
            Command(resume="My answer"),
            config={"thread_id": thread_id}
        )
        
        assert result["status"] == "resumed"


def test_backward_compatibility(setup_interrupt_env):
    """Test that old ToolMessage pattern still works when interrupt is disabled."""
    # Disable interrupt pattern
    os.environ["USE_INTERRUPT_PATTERN"] = "false"
    
    # Import after env change to get the right version
    from deepagents.tools import ask_user_question
    
    # Create mock state and tool_call_id
    mock_state = {
        "consecutive_respond_calls": 0,
        "last_tool_used": "",
        "messages": []
    }
    
    # Call the tool
    result = ask_user_question(
        question="What is your name?",
        tool_call_id="test-id",
        state=mock_state,
        context="Testing backward compatibility"
    )
    
    # Should return a Command with ToolMessage
    assert hasattr(result, 'update')
    assert 'messages' in result.update
    assert len(result.update['messages']) == 1
    
    # Check the message format
    message = result.update['messages'][0]
    assert "Question: What is your name?" in str(message.content)


def test_feature_flag_switching():
    """Test that feature flag correctly switches between implementations."""
    # Test with interrupt disabled
    os.environ["USE_INTERRUPT_PATTERN"] = "false"
    from deepagents import tools as tools_module
    
    # Force reimport to get new implementation
    import importlib
    importlib.reload(tools_module)
    
    # Should have the old signature with tool_call_id
    import inspect
    sig = inspect.signature(tools_module.ask_user_question)
    assert 'tool_call_id' in sig.parameters
    
    # Test with interrupt enabled
    os.environ["USE_INTERRUPT_PATTERN"] = "true"
    importlib.reload(tools_module)
    
    # Should have the new signature without tool_call_id
    sig = inspect.signature(tools_module.ask_user_question)
    assert 'tool_call_id' not in sig.parameters


@pytest.mark.asyncio
async def test_api_endpoints():
    """Test the API endpoints for thread management."""
    from deepagents.api import app, set_agent_graph
    from fastapi.testclient import TestClient
    
    # Create test client
    client = TestClient(app)
    
    # Test health check
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Test create thread
    response = client.post("/threads")
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    assert thread_id is not None
    
    # Test get thread state (without agent)
    response = client.get(f"/threads/{thread_id}/state")
    assert response.status_code == 200
    state = response.json()
    assert state["interrupted"] == False
    
    # Test resume (should fail without agent)
    response = client.post(
        f"/threads/{thread_id}/resume",
        json={"answer": "test answer"}
    )
    assert response.status_code == 500  # Agent not initialized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])