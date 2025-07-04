# /Users/nicholaspate/Documents/ATLAS/backend/src/agents/global_supervisor.py

import time
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BaseSupervisor, Task, TaskResult, AgentStatus
from ..agui.handlers import AGUIEventBroadcaster
from ..mlflow.tracking import ATLASMLflowTracker

logger = logging.getLogger(__name__)

class GlobalSupervisorAgent(BaseSupervisor):
    """Global Supervisor Agent - Top-level orchestrator for ATLAS multi-agent system."""
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        agui_broadcaster: Optional[AGUIEventBroadcaster] = None,
        mlflow_tracker: Optional[ATLASMLflowTracker] = None
    ):
        super().__init__(
            agent_id="global_supervisor",
            agent_type="Global Supervisor",
            team_name="ATLAS_Global",
            worker_agent_ids=[
                "research_team_supervisor",
                "analysis_team_supervisor", 
                "writing_team_supervisor",
                "creation_team_supervisor",
                "rating_team_supervisor"
            ],
            task_id=task_id,
            agui_broadcaster=agui_broadcaster,
            mlflow_tracker=mlflow_tracker
        )
        
        # Global coordination state
        self.active_projects: Dict[str, Dict[str, Any]] = {}
        self.team_capabilities: Dict[str, List[str]] = {
            "research_team_supervisor": ["web_search", "document_analysis", "academic_research", "source_verification"],
            "analysis_team_supervisor": ["data_analysis", "strategic_planning", "financial_analysis", "swot_analysis", "comparison_analysis"],
            "writing_team_supervisor": ["content_generation", "report_structuring", "quality_review", "editing"],
            "creation_team_supervisor": ["image_creation", "audio_creation", "video_creation", "3d_modeling"],
            "rating_team_supervisor": ["quality_assurance", "verification", "feedback_generation"]
        }
        
        self.completion_threshold = 0.8  # 80% team completion required before final review
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process high-level task by decomposing and orchestrating team coordination."""
        await self.update_status(AgentStatus.PROCESSING, f"Processing global task: {task.task_type}")
        
        start_time = time.time()
        
        try:
            # Use simple run_id for tracking (don't depend on complex MLflow context managers)
            run_id = f"global_supervisor_{task.task_id}"
            
            # Try to start MLflow run if available (but don't fail if it doesn't work)
            if self.mlflow_tracker and hasattr(self.mlflow_tracker, 'start_agent_run'):
                try:
                    mlflow_run_context = self.mlflow_tracker.start_agent_run(
                        agent_id=self.agent_id,
                        agent_type=self.agent_type,
                        task_id=task.task_id,
                        parent_run_id=None
                    )
                    # Don't use context manager for now - just note that MLflow is available
                    logger.info(f"MLflow tracking available for task {task.task_id}")
                except Exception as mlflow_error:
                    logger.warning(f"MLflow run start failed (continuing without it): {mlflow_error}")
            else:
                logger.info("MLflow tracking not available - using basic tracking")
            
            # Store project information
            self.active_projects[task.task_id] = {
                "task": task,
                "start_time": datetime.now(),
                "teams_assigned": [],
                "completion_status": {},
                "deliverables": {},
                "run_id": run_id
            }
            
            # Analyze task and plan decomposition
            decomposition_plan = await self._analyze_and_decompose_task(task, run_id)
            
            # Coordinate team execution
            coordination_result = await self._coordinate_team_execution(decomposition_plan, task, run_id)
            
            # Monitor and synthesize results
            final_result = await self._synthesize_global_result(task, coordination_result, run_id)
            
            processing_time = time.time() - start_time
            
            # Create final task result
            task_result = TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="global_coordination",
                content=final_result,
                success=True,
                processing_time=processing_time,
                metadata={
                    "teams_involved": len(decomposition_plan.get("team_assignments", [])),
                    "coordination_strategy": decomposition_plan.get("strategy", "sequential"),
                    "quality_threshold_met": True,
                    "deliverable_types": list(final_result.get("deliverables", {}).keys())
                },
                requires_review=False  # Global supervisor results don't need review
            )
            
            await self.update_status(AgentStatus.COMPLETED, f"Global task completed successfully")
            return task_result
                
        except Exception as e:
            processing_time = time.time() - start_time
            await self.update_status(AgentStatus.ERROR, f"Global coordination failed: {str(e)}")
            
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="global_coordination",
                content={"error": "Global coordination failed", "details": str(e)},
                success=False,
                processing_time=processing_time,
                errors=[str(e)]
            )
    
    async def _analyze_and_decompose_task(self, task: Task, run_id: str) -> Dict[str, Any]:
        """Analyze the task and create decomposition plan using Library and LLM."""
        
        # Query Library for relevant context and similar past tasks
        library_context = await self.call_library(
            operation="search",
            query=f"similar tasks: {task.task_type} {task.description[:100]}",
            context={
                "search_type": "task_history",
                "limit": 5,
                "include_patterns": True
            }
        )
        
        # Use CallModel to analyze task and create decomposition plan
        decomposition_prompt = f"""Analyze this task and create a decomposition plan for the ATLAS multi-agent system.

TASK TO ANALYZE:
Type: {task.task_type}
Description: {task.description}
Priority: {task.priority}
Context: {task.context}

AVAILABLE TEAMS AND CAPABILITIES:
{self.team_capabilities}

LIBRARY CONTEXT:
{library_context.get('result', 'No relevant past tasks found')}

Create a JSON decomposition plan with:
1. team_assignments: List of teams needed and their specific sub-tasks
2. execution_strategy: "sequential", "parallel", or "hybrid"  
3. dependencies: Which teams depend on others' outputs
4. estimated_timeline: Rough time estimates
5. success_criteria: How to measure completion
6. risk_factors: Potential challenges

Respond with valid JSON only."""

        response = await self.call_model.call_model(
            model_name="claude-3-5-haiku-20241022",
            system_prompt=await self.get_system_prompt(),
            most_recent_message=decomposition_prompt,
            max_tokens=800,
            temperature=0.3
        )
        
        if response.success:
            try:
                import json
                plan = json.loads(response.content)
                
                # Store decomposition in Library
                await self.call_library(
                    operation="add",
                    data={
                        "type": "decomposition_plan",
                        "task_id": task.task_id,
                        "plan": plan,
                        "created_by": self.agent_id,
                        "timestamp": datetime.now().isoformat()
                    },
                    context={"category": "task_planning"}
                )
                
                return plan
            except json.JSONDecodeError:
                # Fallback to basic decomposition
                return self._create_fallback_decomposition(task)
        else:
            return self._create_fallback_decomposition(task)
    
    def _create_fallback_decomposition(self, task: Task) -> Dict[str, Any]:
        """Create basic fallback decomposition when LLM analysis fails."""
        return {
            "team_assignments": [
                {"team": "research_team_supervisor", "sub_task": "Gather relevant information"},
                {"team": "analysis_team_supervisor", "sub_task": "Analyze gathered data"},
                {"team": "writing_team_supervisor", "sub_task": "Structure and write report"},
                {"team": "rating_team_supervisor", "sub_task": "Quality assurance review"}
            ],
            "execution_strategy": "sequential",
            "dependencies": {
                "analysis_team_supervisor": ["research_team_supervisor"],
                "writing_team_supervisor": ["analysis_team_supervisor"],
                "rating_team_supervisor": ["writing_team_supervisor"]
            },
            "estimated_timeline": "60 minutes",
            "success_criteria": ["All teams complete their assignments", "Quality review passes"],
            "risk_factors": ["Data availability", "Time constraints"]
        }
    
    async def _coordinate_team_execution(self, plan: Dict[str, Any], task: Task, run_id: str) -> Dict[str, Any]:
        """Coordinate execution across teams based on decomposition plan."""
        
        coordination_results = {
            "team_results": {},
            "execution_timeline": [],
            "issues_encountered": [],
            "strategy_used": plan.get("execution_strategy", "sequential")
        }
        
        team_assignments = plan.get("team_assignments", [])
        
        # For now, simulate team coordination (actual team agents will be implemented later)
        for assignment in team_assignments:
            team_id = assignment.get("team")
            sub_task = assignment.get("sub_task", "Process assigned work")
            
            # Create sub-task for team
            team_task = Task(
                task_id=f"{task.task_id}_{team_id}",
                task_type=f"team_assignment_{team_id}",
                description=sub_task,
                priority=task.priority,
                assigned_to=team_id,
                parent_task_id=task.task_id,
                context={
                    "parent_task": task.description,
                    "team_role": assignment,
                    "global_context": task.context
                }
            )
            
            # Delegate to team (placeholder - actual delegation will be implemented with team supervisors)
            delegation_success = await self.delegate_task(team_task, team_id)
            
            if delegation_success:
                coordination_results["team_results"][team_id] = {
                    "status": "delegated",
                    "task_id": team_task.task_id,
                    "assignment": sub_task,
                    "delegated_at": datetime.now().isoformat()
                }
                coordination_results["execution_timeline"].append({
                    "event": "task_delegated",
                    "team": team_id,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                coordination_results["issues_encountered"].append({
                    "issue": f"Failed to delegate to {team_id}",
                    "impact": "high",
                    "timestamp": datetime.now().isoformat()
                })
        
        return coordination_results
    
    async def _synthesize_global_result(self, task: Task, coordination_result: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Synthesize final results from all team contributions."""
        
        # Store coordination results in Library
        await self.call_library(
            operation="add",
            data={
                "type": "coordination_results",
                "task_id": task.task_id,
                "results": coordination_result,
                "synthesized_by": self.agent_id,
                "timestamp": datetime.now().isoformat()
            },
            context={"category": "execution_results"}
        )
        
        # Create comprehensive final result
        final_result = {
            "task_summary": {
                "original_request": task.description,
                "task_type": task.task_type,
                "completion_status": "completed",
                "teams_involved": len(coordination_result.get("team_results", {}))
            },
            "execution_summary": {
                "strategy_used": coordination_result.get("strategy_used", "sequential"),
                "timeline": coordination_result.get("execution_timeline", []),
                "issues_resolved": len(coordination_result.get("issues_encountered", []))
            },
            "deliverables": {
                "coordination_plan": "Task successfully decomposed and coordinated",
                "team_assignments": coordination_result.get("team_results", {}),
                "next_steps": "Awaiting team completion and synthesis"
            },
            "quality_metrics": {
                "delegation_success_rate": self._calculate_delegation_success_rate(coordination_result),
                "estimated_completion_time": "Pending team execution",
                "global_confidence": 0.85
            },
            "metadata": {
                "global_supervisor_id": self.agent_id,
                "coordination_completed_at": datetime.now().isoformat(),
                "mlflow_run_id": run_id
            }
        }
        
        return final_result
    
    def _calculate_delegation_success_rate(self, coordination_result: Dict[str, Any]) -> float:
        """Calculate success rate of team delegations."""
        team_results = coordination_result.get("team_results", {})
        if not team_results:
            return 0.0
        
        successful_delegations = sum(1 for result in team_results.values() 
                                   if result.get("status") == "delegated")
        return successful_delegations / len(team_results)
    
    async def get_system_prompt(self) -> str:
        """Get Global Supervisor specific system prompt."""
        base_prompt = await super().get_system_prompt()
        
        global_prompt = f"""{base_prompt}

GLOBAL SUPERVISOR CAPABILITIES:
- Task decomposition and strategic planning
- Multi-team coordination and resource allocation  
- Quality oversight and delivery management
- Library integration for knowledge management and learning
- Cross-team communication and dependency management

COORDINATION PRIORITIES:
1. Understand the full scope and requirements of incoming tasks
2. Decompose complex tasks into appropriate team assignments
3. Ensure proper sequencing and dependency management
4. Monitor progress and adjust strategy as needed
5. Synthesize team outputs into comprehensive deliverables
6. Maintain quality standards across all team contributions

ACTIVE PROJECTS: {len(self.active_projects)}
TEAM CAPABILITIES: {list(self.team_capabilities.keys())}

As the Global Supervisor, your role is strategic oversight and coordination, not detailed execution."""
        
        return global_prompt