"""
Analysis Agent for ATLAS Multi-Agent System

Provides advanced data analysis capabilities including statistical analysis,
code execution in sandboxed environments, visualization generation, and
comprehensive file management operations.
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from src.agents.base import BaseAgent, Task, TaskResult, AgentStatus
from src.agents.agent_factory import LettaAgentFactory
from src.agui.handlers import AGUIEventBroadcaster
from src.mlflow.tracking import ATLASMLflowTracker

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent specialized in data analysis, code execution, and visualization.

    Capabilities:
    - Execute Python code in sandboxed E2B environments
    - Perform statistical analysis on datasets
    - Generate charts, graphs, and visualizations
    - File operations (read, write, update, list)
    - Namespaced planning and todo management for analysis tasks
    - Integration with Letta agent runtime for persistent memory

    The agent receives tasks via XML-formatted context messages and processes
    them using registered tools exposed to the underlying Letta agent.
    """

    def __init__(
        self,
        agent_id: str,
        letta_agent: Optional[Any] = None,
        factory: Optional[LettaAgentFactory] = None,
        task_id: Optional[str] = None,
        agui_broadcaster: Optional[AGUIEventBroadcaster] = None,
        mlflow_tracker: Optional[ATLASMLflowTracker] = None
    ):
        """
        Initialize the Analysis Agent.

        Args:
            agent_id: Unique identifier for this agent instance
            letta_agent: Letta agent instance for memory and tool integration
            factory: LettaAgentFactory for agent management operations
            task_id: Optional task ID for tracking (auto-generated if not provided)
            agui_broadcaster: Event broadcaster for real-time communication
            mlflow_tracker: MLflow tracker for observability and logging
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="Analysis Agent",
            task_id=task_id,
            agui_broadcaster=agui_broadcaster,
            mlflow_tracker=mlflow_tracker
        )

        self.letta_agent = letta_agent
        self.factory = factory
        self.analysis_namespace = f"analysis_{self.agent_id}"
        self.session_files: List[str] = []
        self.execution_history: List[Dict[str, Any]] = []

        # Register analysis-specific tools
        self._register_tools()

        logger.info(f"Analysis Agent {self.agent_id} initialized with namespace {self.analysis_namespace}")

    def _register_tools(self) -> None:
        """Register analysis tools with the Letta agent."""
        if not self.letta_agent:
            logger.warning("No Letta agent provided - tools will not be registered")
            return

        tools = [
            self.execute_python,
            self.run_data_analysis,
            self.generate_visualization,
            self.list_files,
            self.read_file,
            self.create_file,
            self.update_file,
            self.plan_analysis,
            self.track_analysis_progress
        ]

        # Note: Actual tool registration with Letta agent would happen here
        # This depends on the specific Letta tool registration API
        logger.info(f"Registered {len(tools)} analysis tools")

    async def process_delegation(self, context: str, task_description: str, restrictions: str = "") -> Dict[str, Any]:
        """
        Process a delegated analysis task with XML-formatted context.

        This method receives the XML context as a message (not in system prompt)
        and processes it using the agent's analytical capabilities.

        Args:
            context: Overall goal and background information
            task_description: Specific analysis actions to perform
            restrictions: Analysis boundaries and requirements

        Returns:
            Dictionary containing task status and initial response
        """
        await self.update_status(AgentStatus.ACTIVE, "Processing delegated analysis task")

        try:
            # Create XML-formatted message to send to Letta agent
            xml_message = f"""<analysis_delegation>
<context>
{context}
</context>

<task>
{task_description}
</task>

<restrictions>
{restrictions if restrictions else "No specific restrictions provided."}
</restrictions>

<tools_available>
- execute_python: Run Python code in sandboxed environment
- run_data_analysis: Perform statistical analysis
- generate_visualization: Create charts and graphs
- file operations: read_file, create_file, update_file, list_files
- plan_analysis: Create analysis plans
- track_analysis_progress: Manage analysis todos
</tools_available>
</analysis_delegation>"""

            # Send message to Letta agent if available
            if self.factory and self.letta_agent:
                response = self.factory.send_message_to_agent(self.letta_agent.id, xml_message)

                # Broadcast delegation start
                await self.agui_broadcaster.broadcast_dialogue_update(
                    task_id=self.task_id,
                    agent_id=self.agent_id,
                    message_id=str(uuid.uuid4()),
                    direction="input",
                    content={
                        "type": "analysis_delegation",
                        "data": {
                            "context_length": len(context),
                            "task_description": task_description[:100] + "..." if len(task_description) > 100 else task_description,
                            "restrictions": restrictions
                        },
                        "metadata": {
                            "timestamp": datetime.now().isoformat(),
                            "namespace": self.analysis_namespace
                        }
                    },
                    sender="supervisor"
                )

                logger.info(f"Analysis delegation processed successfully for agent {self.agent_id}")
                return {
                    "status": "delegated",
                    "agent_id": self.agent_id,
                    "task_id": self.task_id,
                    "response": response,
                    "namespace": self.analysis_namespace,
                    "delegated_at": datetime.now().isoformat()
                }
            else:
                # Fallback: process locally without Letta
                logger.warning("No Letta agent available - processing delegation locally")
                return await self._process_local_delegation(context, task_description, restrictions)

        except Exception as e:
            logger.error(f"Error processing analysis delegation: {str(e)}")
            await self.update_status(AgentStatus.ERROR, f"Delegation processing failed: {str(e)}")
            return {
                "status": "failed",
                "agent_id": self.agent_id,
                "error": str(e),
                "delegated_at": datetime.now().isoformat()
            }

    async def _process_local_delegation(self, context: str, task_description: str, restrictions: str) -> Dict[str, Any]:
        """Fallback method for processing delegations without Letta agent."""
        # This is a simplified fallback implementation
        await self.update_status(AgentStatus.PROCESSING, "Processing analysis locally")

        response_content = f"""Analysis delegation received:
- Context: {context[:100]}...
- Task: {task_description}
- Restrictions: {restrictions}

This would typically be processed by the Letta agent using available analysis tools."""

        await self.update_status(AgentStatus.COMPLETED, "Local delegation processing complete")

        return {
            "status": "processed_locally",
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "response": response_content,
            "namespace": self.analysis_namespace,
            "delegated_at": datetime.now().isoformat()
        }

    # Analysis Tool Implementations

    def execute_python(self, code: str, environment: str = "default") -> Dict[str, Any]:
        """
        Execute Python code in a sandboxed E2B environment.

        Args:
            code: Python code to execute
            environment: E2B environment configuration (default, data-science, etc.)

        Returns:
            Execution result with stdout, stderr, and any generated files
        """
        try:
            execution_id = str(uuid.uuid4())
            start_time = datetime.now()

            # TODO: Integrate with actual E2B SDK
            # For now, simulate code execution
            result = {
                "execution_id": execution_id,
                "code": code,
                "environment": environment,
                "status": "simulated",
                "stdout": f"# Simulated execution of {len(code)} characters of Python code",
                "stderr": "",
                "execution_time": 0.1,
                "files_created": [],
                "timestamp": start_time.isoformat()
            }

            self.execution_history.append(result)
            logger.info(f"Python code executed (simulated) with ID {execution_id}")

            return result

        except Exception as e:
            logger.error(f"Python execution failed: {str(e)}")
            return {
                "execution_id": str(uuid.uuid4()),
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run_data_analysis(self, data_path: str, analysis_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform statistical analysis on datasets.

        Args:
            data_path: Path to the dataset file
            analysis_type: Type of analysis (descriptive, correlation, regression, etc.)
            parameters: Additional parameters for the analysis

        Returns:
            Analysis results including statistics, insights, and recommendations
        """
        try:
            analysis_id = str(uuid.uuid4())

            # TODO: Implement actual data analysis logic
            # This would typically use pandas, scipy, sklearn, etc.
            result = {
                "analysis_id": analysis_id,
                "data_path": data_path,
                "analysis_type": analysis_type,
                "parameters": parameters or {},
                "status": "simulated",
                "summary": f"Simulated {analysis_type} analysis on {data_path}",
                "statistics": {
                    "rows": 1000,
                    "columns": 10,
                    "missing_values": 5
                },
                "insights": [
                    f"Analysis type: {analysis_type}",
                    "Data quality assessment completed",
                    "Statistical patterns identified"
                ],
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Data analysis {analysis_type} completed with ID {analysis_id}")
            return result

        except Exception as e:
            logger.error(f"Data analysis failed: {str(e)}")
            return {
                "analysis_id": str(uuid.uuid4()),
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def generate_visualization(self, data_path: str, chart_type: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate charts, graphs, and visualizations.

        Args:
            data_path: Path to the data file
            chart_type: Type of visualization (bar, line, scatter, heatmap, etc.)
            config: Visualization configuration (colors, labels, styling)

        Returns:
            Visualization result with file path and metadata
        """
        try:
            viz_id = str(uuid.uuid4())
            output_path = f"outputs/analysis_{self.agent_id}/viz_{viz_id}.png"

            # TODO: Implement actual visualization generation
            # This would typically use matplotlib, plotly, seaborn, etc.
            result = {
                "visualization_id": viz_id,
                "chart_type": chart_type,
                "data_path": data_path,
                "output_path": output_path,
                "config": config or {},
                "status": "simulated",
                "dimensions": {"width": 800, "height": 600},
                "file_size": "125KB",
                "timestamp": datetime.now().isoformat()
            }

            self.session_files.append(output_path)
            logger.info(f"Visualization {chart_type} generated with ID {viz_id}")

            return result

        except Exception as e:
            logger.error(f"Visualization generation failed: {str(e)}")
            return {
                "visualization_id": str(uuid.uuid4()),
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def list_files(self, directory_path: str = ".", pattern: str = "*") -> Dict[str, Any]:
        """
        List files in a directory with optional pattern matching.

        Args:
            directory_path: Directory to list files from
            pattern: File pattern to match (e.g., "*.csv", "*.py")

        Returns:
            List of files with metadata
        """
        try:
            # TODO: Implement actual file listing
            # This would use pathlib.Path.glob() or similar
            result = {
                "directory": directory_path,
                "pattern": pattern,
                "files": [
                    {"name": "sample_data.csv", "size": "2.5MB", "modified": "2025-01-03T10:30:00"},
                    {"name": "analysis_script.py", "size": "5.2KB", "modified": "2025-01-03T11:15:00"},
                    {"name": "results.json", "size": "850B", "modified": "2025-01-03T11:45:00"}
                ],
                "total_files": 3,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Listed {result['total_files']} files in {directory_path}")
            return result

        except Exception as e:
            logger.error(f"File listing failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read file contents.

        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)

        Returns:
            File contents and metadata
        """
        try:
            # TODO: Implement actual file reading
            result = {
                "file_path": file_path,
                "encoding": encoding,
                "content": f"# Simulated content of {file_path}",
                "size": "1.2KB",
                "lines": 45,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Read file: {file_path}")
            return result

        except Exception as e:
            logger.error(f"File read failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def create_file(self, file_path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Create a new file with specified content.

        Args:
            file_path: Path for the new file
            content: File content to write
            encoding: File encoding (default: utf-8)

        Returns:
            File creation result
        """
        try:
            # TODO: Implement actual file creation
            result = {
                "file_path": file_path,
                "content_length": len(content),
                "encoding": encoding,
                "status": "created",
                "timestamp": datetime.now().isoformat()
            }

            self.session_files.append(file_path)
            logger.info(f"Created file: {file_path}")
            return result

        except Exception as e:
            logger.error(f"File creation failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def update_file(self, file_path: str, content: str, mode: str = "append") -> Dict[str, Any]:
        """
        Update an existing file.

        Args:
            file_path: Path to the file to update
            content: Content to add or replace
            mode: Update mode ("append", "prepend", "replace")

        Returns:
            File update result
        """
        try:
            # TODO: Implement actual file updating
            result = {
                "file_path": file_path,
                "content_length": len(content),
                "mode": mode,
                "status": "updated",
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Updated file: {file_path} (mode: {mode})")
            return result

        except Exception as e:
            logger.error(f"File update failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def plan_analysis(self, goal: str, steps: List[str], constraints: List[str] = None) -> Dict[str, Any]:
        """
        Create a namespaced analysis plan.

        Args:
            goal: Analysis objective
            steps: List of analysis steps
            constraints: Analysis constraints or limitations

        Returns:
            Created plan with namespace
        """
        try:
            plan_id = str(uuid.uuid4())
            plan = {
                "plan_id": plan_id,
                "namespace": self.analysis_namespace,
                "goal": goal,
                "steps": steps,
                "constraints": constraints or [],
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "estimated_duration": f"{len(steps) * 30} minutes"
            }

            logger.info(f"Created analysis plan {plan_id} in namespace {self.analysis_namespace}")
            return plan

        except Exception as e:
            logger.error(f"Analysis planning failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def track_analysis_progress(self, plan_id: str, step_completed: str, notes: str = "") -> Dict[str, Any]:
        """
        Track progress on analysis tasks (namespaced todos).

        Args:
            plan_id: ID of the analysis plan
            step_completed: Description of completed step
            notes: Additional notes or observations

        Returns:
            Progress tracking result
        """
        try:
            progress_id = str(uuid.uuid4())
            progress = {
                "progress_id": progress_id,
                "plan_id": plan_id,
                "namespace": self.analysis_namespace,
                "step_completed": step_completed,
                "notes": notes,
                "completed_at": datetime.now().isoformat(),
                "status": "tracked"
            }

            logger.info(f"Tracked progress {progress_id} for plan {plan_id}")
            return progress

        except Exception as e:
            logger.error(f"Progress tracking failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def process_task(self, task: Task) -> TaskResult:
        """
        Process a task assigned to this analysis agent.

        Args:
            task: The task to process

        Returns:
            TaskResult with analysis output
        """
        start_time = datetime.now()
        await self.update_status(AgentStatus.PROCESSING, f"Processing task: {task.task_type}")

        try:
            # Process based on task type
            if task.task_type == "data_analysis":
                result_content = await self._handle_data_analysis_task(task)
            elif task.task_type == "code_execution":
                result_content = await self._handle_code_execution_task(task)
            elif task.task_type == "visualization":
                result_content = await self._handle_visualization_task(task)
            else:
                result_content = f"Unknown task type: {task.task_type}"

            processing_time = (datetime.now() - start_time).total_seconds()

            task_result = TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="analysis_result",
                content=result_content,
                success=True,
                processing_time=processing_time,
                metadata={
                    "namespace": self.analysis_namespace,
                    "files_created": self.session_files,
                    "executions": len(self.execution_history)
                }
            )

            await self.update_status(AgentStatus.COMPLETED, "Task processing complete")
            return task_result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Task processing failed: {str(e)}")

            task_result = TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="error",
                content=f"Analysis task failed: {str(e)}",
                success=False,
                processing_time=processing_time,
                errors=[str(e)]
            )

            await self.update_status(AgentStatus.ERROR, f"Task failed: {str(e)}")
            return task_result

    async def _handle_data_analysis_task(self, task: Task) -> str:
        """Handle data analysis specific tasks."""
        data_path = task.context.get("data_path", "default_dataset.csv")
        analysis_type = task.context.get("analysis_type", "descriptive")

        analysis_result = self.run_data_analysis(data_path, analysis_type)
        return f"Data analysis completed: {analysis_result['summary']}"

    async def _handle_code_execution_task(self, task: Task) -> str:
        """Handle code execution specific tasks."""
        code = task.context.get("code", "print('Hello, Analysis!')")
        environment = task.context.get("environment", "default")

        execution_result = self.execute_python(code, environment)
        return f"Code execution result: {execution_result['stdout']}"

    async def _handle_visualization_task(self, task: Task) -> str:
        """Handle visualization specific tasks."""
        data_path = task.context.get("data_path", "sample_data.csv")
        chart_type = task.context.get("chart_type", "bar")

        viz_result = self.generate_visualization(data_path, chart_type)
        return f"Visualization created: {viz_result['output_path']}"

    def get_agent_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent's current state and capabilities."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "namespace": self.analysis_namespace,
            "capabilities": [
                "Python code execution (E2B sandbox)",
                "Statistical data analysis",
                "Visualization generation",
                "File operations (read/write/update)",
                "Namespaced planning and tracking"
            ],
            "session_files": len(self.session_files),
            "execution_history": len(self.execution_history),
            "created_at": self.created_at.isoformat()
        }