import unittest
from unittest.mock import patch, MagicMock
import os
import json

# Mock the config class
class MockMLflowConfig:
    def __init__(self, tracking_uri):
        self.tracking_uri = tracking_uri

# Mock the cost calculator
from src.utils.cost_calculator import get_cost_and_pricing_details

# Import the class to be tested
from src.mlflow.tracking import ATLASMLflowTracker

class TestATLASMLflowTracker(unittest.TestCase):

    def setUp(self):
        """Set up a mock MLflow client and tracker instance."""
        self.mock_config = MockMLflowConfig(tracking_uri="sqlite:///:memory:")
        self.tracker = ATLASMLflowTracker(self.mock_config)
        self.tracker.client = MagicMock()

    @patch('mlflow.start_run')
    def test_start_task_run(self, mock_start_run):
        """Test the creation of a parent task run."""
        mock_run = MagicMock()
        mock_run.info.run_id = "test_task_run_id"
        mock_start_run.return_value.__enter__.return_value = mock_run

        task_id = "task_123"
        task_metadata = {
            'user_id': 'user_abc',
            'initial_prompt': 'Analyze the market trends.',
            'task_type': 'Analysis',
            'teams_involved': ['Research', 'Analysis']
        }

        run_id = self.tracker.start_task_run(task_id, task_metadata)

        self.assertEqual(run_id, "test_task_run_id")
        mlflow.set_experiment.assert_called_with(f"ATLAS_Task_{task_id}")
        mock_start_run.assert_called_with(run_name="Global_Supervisor_Run")
        mlflow.log_params.assert_called_with({
            'task_type': 'Analysis',
            'user_id': 'user_abc'
        })
        mlflow.log_text.assert_any_call('Analyze the market trends.', artifact_file='initial_prompt.txt')
        mlflow.log_text.assert_any_call(json.dumps(['Research', 'Analysis'], indent=2), artifact_file='teams.json')

    @patch('mlflow.start_run')
    def test_start_agent_run(self, mock_start_run):
        """Test the creation of a nested agent run."""
        mock_run = MagicMock()
        mock_run.info.run_id = "test_agent_run_id"
        mock_start_run.return_value.__enter__.return_value = mock_run

        parent_run_id = "test_task_run_id"
        agent_id = "research_worker_1"
        agent_config = {
            'agent_type': 'Worker',
            'team': 'Research',
            'model_name': 'gpt-4',
            'persona_prompt': 'You are a research assistant.',
            'tools_available': ['search', 'read_file']
        }

        run_id = self.tracker.start_agent_run(parent_run_id, agent_id, agent_config)

        self.assertEqual(run_id, "test_agent_run_id")
        mock_start_run.assert_called_with(run_name=agent_id, nested=True, run_id=parent_run_id)
        mlflow.log_params.assert_called_with({
            'agent_type': 'Worker',
            'team': 'Research',
            'model_name': 'gpt-4'
        })
        mlflow.log_text.assert_any_call('You are a research assistant.', artifact_file='persona.txt')
        mlflow.log_text.assert_any_call(json.dumps(['search', 'read_file'], indent=2), artifact_file='tools.json')
        mlflow.set_tag.assert_any_call('atlas.team', 'Research')
        mlflow.set_tag.assert_any_call('atlas.agent_type', 'Worker')

    @patch('backend.src.utils.cost_calculator.get_cost_and_pricing_details')
    @patch('mlflow.start_run')
    def test_log_agent_transaction(self, mock_start_run, mock_get_cost):
        """Test logging of an agent transaction."""
        mock_get_cost.return_value = (0.123, {'provider': 'OpenAI', 'input_cost_per_million_tokens': 10.0, 'output_cost_per_million_tokens': 30.0})

        agent_run_id = "test_agent_run_id"
        model_name = "gpt-4-turbo"
        input_tokens = 1000
        output_tokens = 2000
        artifacts = {"output.txt": "This is the agent output."}

        self.tracker.log_agent_transaction(agent_run_id, model_name, input_tokens, output_tokens, artifacts, step=1)

        mock_start_run.assert_called_with(run_id=agent_run_id)
        mlflow.log_param.assert_called_with("model_provider", "OpenAI")
        mlflow.log_metrics.assert_called_with({
            'input_tokens': 1000,
            'output_tokens': 2000,
            'total_tokens': 3000,
            'cost_per_million_input_tokens': 10.0,
            'cost_per_million_output_tokens': 30.0,
            'final_cost_usd': 0.123
        }, step=1)
        mlflow.log_text.assert_called_with("This is the agent output.", artifact_file="output.txt")

    @patch('mlflow.start_run')
    def test_log_agent_error(self, mock_start_run):
        """Test logging of an agent error."""
        agent_run_id = "test_agent_run_id"
        try:
            raise ValueError("Test error")
        except ValueError as e:
            error = e

        self.tracker.log_agent_error(agent_run_id, error)

        mock_start_run.assert_called_with(run_id=agent_run_id)
        mlflow.set_tag.assert_called_with("status", "FAILED")
        mlflow.log_params.assert_called_with({
            'error_type': 'ValueError',
            'error_message': 'Test error'
        })
        mlflow.log_text.assert_called_with(unittest.mock.ANY, artifact_file="error_trace.log")

if __name__ == '__main__':
    unittest.main()
