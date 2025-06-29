# LangGraph Comprehensive Guide for ATLAS (2025)

## Overview

LangGraph is a low-level orchestration framework for building stateful, multi-agent applications with Large Language Models. This guide covers implementation for ATLAS multi-agent system with advanced checkpoint management, error handling, and production deployment using the latest 2025 features.

## LangGraph Architecture & Core Concepts

### Execution Model

LangGraph uses a Bulk Synchronous Parallel (BSP) execution model with three phases:

1. **Plan Phase**: Determine which nodes should execute and create executable tasks
2. **Execute Phase**: Run selected tasks concurrently with retry and error recovery
3. **Update Phase**: Apply writes to channels atomically and create checkpoints

### Key Features for Multi-Agent Systems

- **Stateful Execution**: Persistent state across operations with checkpoint management
- **Human-in-the-Loop**: Execution can pause for human feedback or intervention
- **Dynamic Routing**: Conditional logic for complex multi-agent workflows
- **Durable Execution**: Automatic recovery from failures with built-in checkpointing
- **Real-time Streaming**: Stream agent state, model tokens, and tool outputs

## ATLAS LangGraph Implementation

### 1. State Schema Design

```python
# atlas_state.py

from typing import TypedDict, Dict, Any, List, Optional, Annotated
from typing_extensions import NotRequired
from dataclasses import dataclass, field
from datetime import datetime
import uuid

# State reducer functions for handling updates
def update_team_results(current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge team results, with new values taking precedence"""
    updated = current.copy()
    updated.update(new)
    return updated

def append_to_list(current: List[Any], new: List[Any]) -> List[Any]:
    """Append new items to existing list"""
    return current + new

def merge_context(current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge context dictionaries"""
    def deep_merge(dict1, dict2):
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    return deep_merge(current, new)

# Core ATLAS State Schema
class ATLASState(TypedDict):
    """Comprehensive state schema for ATLAS multi-agent workflows"""
    
    # Task Identification
    task_id: str
    task_description: str
    task_type: str  # "research", "analysis", "strategic_planning", etc.
    task_priority: str  # "low", "normal", "high", "urgent"
    user_id: str
    
    # Workflow State
    current_step: str
    workflow_stage: str  # "initialization", "execution", "review", "completed"
    completed_teams: Annotated[List[str], append_to_list]
    active_agents: List[str]
    
    # Team Results (with custom reducer for merging)
    team_results: Annotated[Dict[str, Any], update_team_results]
    
    # Context and Memory
    global_context: Annotated[Dict[str, Any], merge_context]
    shared_knowledge: Annotated[Dict[str, Any], merge_context]
    user_inputs: Annotated[List[Dict[str, Any]], append_to_list]
    
    # Quality and Performance Tracking
    quality_scores: Dict[str, float]
    performance_metrics: Dict[str, Any]
    cost_tracking: Dict[str, float]
    
    # Error Handling
    error_log: Annotated[List[Dict[str, Any]], append_to_list]
    retry_count: Dict[str, int]
    escalations: Annotated[List[Dict[str, Any]], append_to_list]
    
    # Workflow Control
    human_intervention_required: bool
    approval_status: Optional[str]  # "pending", "approved", "rejected"
    checkpoint_data: Dict[str, Any]
    
    # Output Management
    intermediate_outputs: Dict[str, Any]
    final_output: NotRequired[Dict[str, Any]]
    
    # Metadata
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]

@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    agent_id: str
    agent_type: str  # "supervisor", "worker", "specialist"
    team: str
    model_provider: str  # "anthropic", "openai", "google", "groq"
    model_name: str
    tools: List[str]
    persona_file: str
    max_tokens: int = 100000
    temperature: float = 0.1
    timeout: int = 300
    retry_attempts: int = 3
    escalation_target: Optional[str] = None

@dataclass
class TeamConfig:
    """Configuration for agent teams"""
    team_name: str
    supervisor_config: AgentConfig
    worker_configs: List[AgentConfig]
    coordination_strategy: str  # "sequential", "parallel", "hybrid"
    quality_threshold: float = 4.0
    max_parallel_workers: int = 3

class WorkflowConfig:
    """Global workflow configuration"""
    
    def __init__(self):
        self.teams = {
            "research": TeamConfig(
                team_name="research",
                supervisor_config=AgentConfig(
                    agent_id="research_supervisor",
                    agent_type="supervisor",
                    team="research",
                    model_provider="anthropic",
                    model_name="claude-3-opus",
                    tools=["worker_coordination", "web_search", "document_analysis"],
                    persona_file="personas/research_supervisor.md"
                ),
                worker_configs=[
                    AgentConfig(
                        agent_id="research_worker_web",
                        agent_type="worker",
                        team="research",
                        model_provider="anthropic",
                        model_name="claude-3-sonnet",
                        tools=["web_search", "tavily_search", "firecrawl"],
                        persona_file="personas/research_worker_web.md"
                    ),
                    AgentConfig(
                        agent_id="research_worker_docs",
                        agent_type="worker",
                        team="research",
                        model_provider="anthropic",
                        model_name="claude-3-sonnet",
                        tools=["document_analysis", "pdf_parser", "citation_extractor"],
                        persona_file="personas/research_worker_docs.md"
                    )
                ],
                coordination_strategy="parallel"
            ),
            "analysis": TeamConfig(
                team_name="analysis",
                supervisor_config=AgentConfig(
                    agent_id="analysis_supervisor",
                    agent_type="supervisor",
                    team="analysis",
                    model_provider="anthropic",
                    model_name="claude-3-opus",
                    tools=["worker_coordination", "statistical_analysis", "framework_selection"],
                    persona_file="personas/analysis_supervisor.md"
                ),
                worker_configs=[
                    AgentConfig(
                        agent_id="analysis_worker_quantitative",
                        agent_type="worker",
                        team="analysis",
                        model_provider="openai",
                        model_name="gpt-4-turbo",
                        tools=["statistical_analysis", "data_visualization", "financial_modeling"],
                        persona_file="personas/analysis_worker_quant.md"
                    ),
                    AgentConfig(
                        agent_id="analysis_worker_qualitative",
                        agent_type="worker",
                        team="analysis",
                        model_provider="anthropic",
                        model_name="claude-3-sonnet",
                        tools=["swot_analysis", "framework_analysis", "debate_generation"],
                        persona_file="personas/analysis_worker_qual.md"
                    )
                ],
                coordination_strategy="sequential"
            ),
            "writing": TeamConfig(
                team_name="writing",
                supervisor_config=AgentConfig(
                    agent_id="writing_supervisor",
                    agent_type="supervisor",
                    team="writing",
                    model_provider="anthropic",
                    model_name="claude-3-opus",
                    tools=["worker_coordination", "document_generation", "style_guide"],
                    persona_file="personas/writing_supervisor.md"
                ),
                worker_configs=[
                    AgentConfig(
                        agent_id="writing_worker_content",
                        agent_type="worker",
                        team="writing",
                        model_provider="anthropic",
                        model_name="claude-3-sonnet",
                        tools=["content_generation", "markdown_formatting", "citation_management"],
                        persona_file="personas/writing_worker_content.md"
                    ),
                    AgentConfig(
                        agent_id="writing_worker_editor",
                        agent_type="worker",
                        team="writing",
                        model_provider="anthropic",
                        model_name="claude-3-sonnet",
                        tools=["content_editing", "style_checking", "fact_verification"],
                        persona_file="personas/writing_worker_editor.md"
                    )
                ],
                coordination_strategy="sequential"
            ),
            "rating": TeamConfig(
                team_name="rating",
                supervisor_config=AgentConfig(
                    agent_id="rating_supervisor",
                    agent_type="supervisor",
                    team="rating",
                    model_provider="anthropic",
                    model_name="claude-3-opus",
                    tools=["worker_coordination", "quality_assessment", "librarian_tools"],
                    persona_file="personas/rating_supervisor.md"
                ),
                worker_configs=[
                    AgentConfig(
                        agent_id="rating_worker_quality",
                        agent_type="worker",
                        team="rating",
                        model_provider="anthropic",
                        model_name="claude-3-sonnet",
                        tools=["quality_scoring", "criteria_evaluation", "improvement_suggestions"],
                        persona_file="personas/rating_worker_quality.md"
                    ),
                    AgentConfig(
                        agent_id="librarian_agent",
                        agent_type="specialist",
                        team="rating",
                        model_provider="anthropic",
                        model_name="claude-3-opus",
                        tools=["knowledge_validation", "fact_checking", "knowledge_storage"],
                        persona_file="personas/librarian_agent.md"
                    )
                ],
                coordination_strategy="parallel"
            )
        }
```

### 2. Enhanced LangGraph Workflow Implementation

```python
# atlas_langgraph_workflow.py

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import ToolNode
from typing import Dict, Any, List, Literal
import asyncio
import time
import uuid
import json
from datetime import datetime
import logging
from atlas_state import ATLASState, WorkflowConfig, AgentConfig
from agent_manager import ATLASAgentManager
from ag_ui_integration import ATLASAGUIBroadcaster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ATLASLangGraphWorkflow:
    """Advanced LangGraph workflow for ATLAS multi-agent system"""
    
    def __init__(
        self, 
        postgres_url: str,
        agent_manager: ATLASAgentManager,
        agui_broadcaster: ATLASAGUIBroadcaster,
        workflow_config: WorkflowConfig
    ):
        self.postgres_url = postgres_url
        self.checkpointer = PostgresSaver.from_conn_string(postgres_url)
        self.agent_manager = agent_manager
        self.agui_broadcaster = agui_broadcaster
        self.workflow_config = workflow_config
        self.workflow_graph = self._create_workflow_graph()
        
        # Performance tracking
        self.execution_metrics = {}
        
    def _create_workflow_graph(self) -> StateGraph:
        """Create comprehensive LangGraph workflow with advanced features"""
        
        # Initialize workflow with state schema
        workflow = StateGraph(ATLASState)
        
        # Core Nodes
        workflow.add_node("global_supervisor", self._global_supervisor_node)
        workflow.add_node("task_initialization", self._task_initialization_node)
        workflow.add_node("human_approval", self._human_approval_node)
        
        # Team Nodes
        workflow.add_node("research_team", self._create_team_node("research"))
        workflow.add_node("analysis_team", self._create_team_node("analysis"))
        workflow.add_node("writing_team", self._create_team_node("writing"))
        workflow.add_node("rating_team", self._create_team_node("rating"))
        
        # Quality Control Nodes
        workflow.add_node("quality_gate", self._quality_gate_node)
        workflow.add_node("final_synthesis", self._final_synthesis_node)
        workflow.add_node("error_recovery", self._error_recovery_node)
        
        # Workflow Edges
        workflow.add_edge(START, "task_initialization")
        workflow.add_edge("task_initialization", "global_supervisor")
        
        # Conditional routing from global supervisor
        workflow.add_conditional_edges(
            "global_supervisor",
            self._route_from_supervisor,
            {
                "research": "research_team",
                "analysis": "analysis_team",
                "writing": "writing_team",
                "rating": "rating_team",
                "quality_gate": "quality_gate",
                "human_approval": "human_approval",
                "error_recovery": "error_recovery",
                "final_synthesis": "final_synthesis",
                "end": END
            }
        )
        
        # Team completion routing
        for team in ["research_team", "analysis_team", "writing_team", "rating_team"]:
            workflow.add_conditional_edges(
                team,
                self._route_after_team_completion,
                {
                    "continue": "global_supervisor",
                    "quality_gate": "quality_gate",
                    "error_recovery": "error_recovery",
                    "human_approval": "human_approval"
                }
            )
        
        # Quality gate routing
        workflow.add_conditional_edges(
            "quality_gate",
            self._route_from_quality_gate,
            {
                "approved": "global_supervisor",
                "revision_needed": "global_supervisor",
                "human_review": "human_approval",
                "final_synthesis": "final_synthesis"
            }
        )
        
        # Human approval routing
        workflow.add_conditional_edges(
            "human_approval",
            self._route_from_human_approval,
            {
                "approved": "global_supervisor",
                "rejected": "error_recovery",
                "modifications": "global_supervisor"
            }
        )
        
        # Error recovery routing
        workflow.add_conditional_edges(
            "error_recovery",
            self._route_from_error_recovery,
            {
                "retry": "global_supervisor",
                "escalate": "human_approval",
                "abort": END
            }
        )
        
        workflow.add_edge("final_synthesis", END)
        
        # Compile with checkpointing and interrupts
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_approval"],  # Always interrupt for human approval
            interrupt_after=["quality_gate"]      # Allow inspection after quality gates
        )
    
    async def _task_initialization_node(self, state: ATLASState) -> ATLASState:
        """Initialize task with comprehensive setup"""
        
        start_time = time.time()
        task_id = state["task_id"]
        
        # Broadcast task initialization
        await self.agui_broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="system",
            status="initializing",
            details="Setting up ATLAS multi-agent workflow"
        )
        
        # Initialize state fields
        updated_state = state.copy()
        updated_state.update({
            "current_step": "initialization",
            "workflow_stage": "initialization",
            "completed_teams": [],
            "active_agents": [],
            "team_results": {},
            "global_context": {
                "task_start_time": start_time,
                "workflow_version": "2.0",
                "checkpoint_enabled": True
            },
            "shared_knowledge": {},
            "user_inputs": [],
            "quality_scores": {},
            "performance_metrics": {},
            "cost_tracking": {},
            "error_log": [],
            "retry_count": {},
            "escalations": [],
            "human_intervention_required": False,
            "approval_status": None,
            "checkpoint_data": {},
            "intermediate_outputs": {},
            "created_at": state.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
            "metadata": {
                **state.get("metadata", {}),
                "initialization_time": time.time() - start_time,
                "teams_configured": list(self.workflow_config.teams.keys()),
                "workflow_complexity": "high"
            }
        })
        
        # Create checkpoint
        updated_state["checkpoint_data"]["initialization"] = {
            "timestamp": datetime.now().isoformat(),
            "state_snapshot": "task_initialized"
        }
        
        # Broadcast completion
        await self.agui_broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="system",
            content=f"✅ Task initialized: {state['task_description']}",
            streaming=False
        )
        
        return updated_state
    
    async def _global_supervisor_node(self, state: ATLASState) -> ATLASState:
        """Enhanced global supervisor with advanced decision making"""
        
        task_id = state["task_id"]
        start_time = time.time()
        
        # Create fresh supervisor agent for this decision
        supervisor_agent_id = await self.agent_manager.create_fresh_agent(
            config=self.workflow_config.teams["research"].supervisor_config,  # Use research supervisor as template
            task_id=task_id,
            specialized_role="global_supervisor"
        )
        
        try:
            # Broadcast supervisor activation
            await self.agui_broadcaster.broadcast_agent_status(
                task_id=task_id,
                agent_id=supervisor_agent_id,
                status="analyzing",
                details="Evaluating current state and planning next actions"
            )
            
            # Prepare context for supervisor
            supervisor_context = self._prepare_supervisor_context(state)
            
            # Get supervisor decision
            decision_result = await self.agent_manager.execute_agent_task(
                agent_id=supervisor_agent_id,
                task_data={
                    "role": "Make strategic coordination decisions for the ATLAS workflow",
                    "context": supervisor_context,
                    "options": self._get_available_options(state),
                    "constraints": {
                        "max_parallel_teams": 2,
                        "quality_threshold": 4.0,
                        "budget_remaining": state["cost_tracking"].get("remaining", 100.0)
                    }
                }
            )
            
            # Parse supervisor decision
            next_action = decision_result.get("next_action", "continue")
            reasoning = decision_result.get("reasoning", "Continuing workflow")
            priority_adjustments = decision_result.get("priority_adjustments", {})
            
            # Broadcast supervisor decision
            await self.agui_broadcaster.broadcast_agent_message(
                task_id=task_id,
                agent_id=supervisor_agent_id,
                content=f"🎯 Decision: {reasoning}",
                streaming=False
            )
            
            # Update state based on decision
            updated_state = state.copy()
            updated_state.update({
                "current_step": next_action,
                "updated_at": datetime.now().isoformat(),
                "metadata": {
                    **state.get("metadata", {}),
                    "last_supervisor_decision": {
                        "action": next_action,
                        "reasoning": reasoning,
                        "timestamp": datetime.now().isoformat(),
                        "decision_time": time.time() - start_time
                    }
                }
            })
            
            # Apply priority adjustments
            if priority_adjustments:
                updated_state["global_context"]["priority_adjustments"] = priority_adjustments
            
            # Update performance metrics
            updated_state["performance_metrics"]["supervisor_decisions"] = \
                updated_state["performance_metrics"].get("supervisor_decisions", 0) + 1
            
            # Create checkpoint
            updated_state["checkpoint_data"]["supervisor_decision"] = {
                "timestamp": datetime.now().isoformat(),
                "decision": next_action,
                "reasoning": reasoning
            }
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in global supervisor: {e}")
            
            # Add to error log
            error_entry = {
                "error": str(e),
                "node": "global_supervisor",
                "timestamp": datetime.now().isoformat(),
                "agent_id": supervisor_agent_id
            }
            
            updated_state = state.copy()
            updated_state["error_log"].append(error_entry)
            updated_state["current_step"] = "error_recovery"
            
            return updated_state
            
        finally:
            # Clean up supervisor agent
            await self.agent_manager.cleanup_agent(supervisor_agent_id, preserve_learnings=True)
    
    def _create_team_node(self, team_name: str):
        """Create dynamic team node with enhanced capabilities"""
        
        async def team_node(state: ATLASState) -> ATLASState:
            task_id = state["task_id"]
            start_time = time.time()
            
            # Get team configuration
            team_config = self.workflow_config.teams[team_name]
            
            # Broadcast team activation
            await self.agui_broadcaster.broadcast_agent_status(
                task_id=task_id,
                agent_id=f"{team_name}_team",
                status="active",
                details=f"Starting {team_name} team operations"
            )
            
            try:
                # Create team supervisor
                supervisor_agent_id = await self.agent_manager.create_fresh_agent(
                    config=team_config.supervisor_config,
                    task_id=task_id
                )
                
                # Create worker agents
                worker_agent_ids = []
                for worker_config in team_config.worker_configs:
                    worker_id = await self.agent_manager.create_fresh_agent(
                        config=worker_config,
                        task_id=task_id
                    )
                    worker_agent_ids.append(worker_id)
                
                # Execute team coordination
                team_result = await self._execute_team_coordination(
                    team_name=team_name,
                    supervisor_id=supervisor_agent_id,
                    worker_ids=worker_agent_ids,
                    task_data=state,
                    coordination_strategy=team_config.coordination_strategy
                )
                
                # Update state with team results
                updated_state = state.copy()
                updated_state["team_results"][team_name] = team_result
                updated_state["completed_teams"].append(team_name)
                updated_state["quality_scores"][team_name] = team_result.get("quality_score", 0)
                updated_state["cost_tracking"][f"{team_name}_cost"] = team_result.get("cost", 0)
                
                # Update performance metrics
                execution_time = time.time() - start_time
                updated_state["performance_metrics"][f"{team_name}_execution_time"] = execution_time
                updated_state["performance_metrics"][f"{team_name}_agent_count"] = len(worker_agent_ids) + 1
                
                # Create checkpoint
                updated_state["checkpoint_data"][f"{team_name}_completion"] = {
                    "timestamp": datetime.now().isoformat(),
                    "quality_score": team_result.get("quality_score", 0),
                    "execution_time": execution_time
                }
                
                # Broadcast team completion
                await self.agui_broadcaster.broadcast_agent_message(
                    task_id=task_id,
                    agent_id=f"{team_name}_supervisor",
                    content=f"✅ {team_name.title()} team completed with quality score: {team_result.get('quality_score', 0):.1f}",
                    streaming=False
                )
                
                return updated_state
                
            except Exception as e:
                logger.error(f"Error in {team_name} team: {e}")
                
                # Handle team error
                error_entry = {
                    "error": str(e),
                    "node": f"{team_name}_team",
                    "timestamp": datetime.now().isoformat(),
                    "team": team_name
                }
                
                updated_state = state.copy()
                updated_state["error_log"].append(error_entry)
                updated_state["retry_count"][team_name] = updated_state["retry_count"].get(team_name, 0) + 1
                
                # Check if retry limit exceeded
                if updated_state["retry_count"][team_name] >= 3:
                    escalation_entry = {
                        "team": team_name,
                        "reason": "max_retries_exceeded",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    updated_state["escalations"].append(escalation_entry)
                    updated_state["human_intervention_required"] = True
                
                return updated_state
                
            finally:
                # Clean up all team agents
                if 'supervisor_agent_id' in locals():
                    await self.agent_manager.cleanup_agent(supervisor_agent_id, preserve_learnings=True)
                if 'worker_agent_ids' in locals():
                    for worker_id in worker_agent_ids:
                        await self.agent_manager.cleanup_agent(worker_id, preserve_learnings=True)
        
        return team_node
    
    async def _execute_team_coordination(
        self,
        team_name: str,
        supervisor_id: str,
        worker_ids: List[str],
        task_data: ATLASState,
        coordination_strategy: str
    ) -> Dict[str, Any]:
        """Execute team coordination with different strategies"""
        
        task_id = task_data["task_id"]
        
        # Prepare team task context
        team_context = {
            "team_objective": self._get_team_objective(team_name, task_data),
            "previous_results": {
                team: results for team, results in task_data["team_results"].items()
                if team != team_name
            },
            "global_context": task_data["global_context"],
            "quality_requirements": {
                "min_score": 4.0,
                "criteria": ["accuracy", "completeness", "relevance", "clarity"]
            }
        }
        
        if coordination_strategy == "parallel":
            return await self._execute_parallel_coordination(
                team_name, supervisor_id, worker_ids, team_context, task_id
            )
        elif coordination_strategy == "sequential":
            return await self._execute_sequential_coordination(
                team_name, supervisor_id, worker_ids, team_context, task_id
            )
        else:  # hybrid
            return await self._execute_hybrid_coordination(
                team_name, supervisor_id, worker_ids, team_context, task_id
            )
    
    async def _execute_parallel_coordination(
        self,
        team_name: str,
        supervisor_id: str,
        worker_ids: List[str],
        team_context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """Execute parallel worker coordination"""
        
        # Supervisor assigns tasks to workers
        task_assignments = await self.agent_manager.execute_agent_task(
            agent_id=supervisor_id,
            task_data={
                "role": f"Assign parallel tasks to {len(worker_ids)} workers",
                "context": team_context,
                "workers": worker_ids,
                "coordination_mode": "parallel"
            }
        )
        
        # Execute worker tasks in parallel
        worker_tasks = []
        for i, worker_id in enumerate(worker_ids):
            assignment = task_assignments.get("assignments", {}).get(worker_id, {})
            if assignment:
                task = self.agent_manager.execute_agent_task(
                    agent_id=worker_id,
                    task_data={
                        "assignment": assignment,
                        "context": team_context,
                        "worker_index": i
                    }
                )
                worker_tasks.append(task)
        
        # Await all worker completions
        worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # Supervisor synthesizes results
        synthesis_result = await self.agent_manager.execute_agent_task(
            agent_id=supervisor_id,
            task_data={
                "role": "Synthesize parallel worker results",
                "worker_results": worker_results,
                "context": team_context,
                "synthesis_mode": "parallel_merge"
            }
        )
        
        return {
            "strategy": "parallel",
            "worker_count": len(worker_ids),
            "individual_results": worker_results,
            "synthesized_result": synthesis_result,
            "quality_score": synthesis_result.get("quality_score", 0),
            "cost": sum(result.get("cost", 0) for result in worker_results if isinstance(result, dict)),
            "execution_time": max(result.get("execution_time", 0) for result in worker_results if isinstance(result, dict))
        }
    
    async def _execute_sequential_coordination(
        self,
        team_name: str,
        supervisor_id: str,
        worker_ids: List[str],
        team_context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """Execute sequential worker coordination"""
        
        accumulated_results = []
        current_context = team_context.copy()
        
        for i, worker_id in enumerate(worker_ids):
            # Supervisor assigns next task based on previous results
            task_assignment = await self.agent_manager.execute_agent_task(
                agent_id=supervisor_id,
                task_data={
                    "role": f"Assign sequential task to worker {i+1}",
                    "context": current_context,
                    "previous_results": accumulated_results,
                    "worker_id": worker_id,
                    "coordination_mode": "sequential"
                }
            )
            
            # Execute worker task
            worker_result = await self.agent_manager.execute_agent_task(
                agent_id=worker_id,
                task_data={
                    "assignment": task_assignment.get("assignment", {}),
                    "context": current_context,
                    "build_upon": accumulated_results
                }
            )
            
            accumulated_results.append(worker_result)
            
            # Update context for next worker
            current_context["accumulated_work"] = accumulated_results
        
        # Supervisor creates final synthesis
        final_result = await self.agent_manager.execute_agent_task(
            agent_id=supervisor_id,
            task_data={
                "role": "Create final synthesis from sequential work",
                "accumulated_results": accumulated_results,
                "context": current_context,
                "synthesis_mode": "sequential_build"
            }
        )
        
        return {
            "strategy": "sequential",
            "worker_count": len(worker_ids),
            "sequential_results": accumulated_results,
            "final_synthesis": final_result,
            "quality_score": final_result.get("quality_score", 0),
            "cost": sum(result.get("cost", 0) for result in accumulated_results),
            "execution_time": sum(result.get("execution_time", 0) for result in accumulated_results)
        }
    
    async def _quality_gate_node(self, state: ATLASState) -> ATLASState:
        """Quality gate with comprehensive validation"""
        
        task_id = state["task_id"]
        
        # Broadcast quality check start
        await self.agui_broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="quality_gate",
            status="evaluating",
            details="Running comprehensive quality validation"
        )
        
        # Evaluate each completed team
        quality_results = {}
        overall_scores = []
        
        for team_name in state["completed_teams"]:
            if team_name in state["team_results"]:
                team_result = state["team_results"][team_name]
                quality_score = team_result.get("quality_score", 0)
                
                quality_results[team_name] = {
                    "score": quality_score,
                    "passed": quality_score >= 4.0,
                    "criteria": team_result.get("quality_criteria", {})
                }
                
                overall_scores.append(quality_score)
        
        # Calculate overall quality
        overall_quality = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        all_passed = all(result["passed"] for result in quality_results.values())
        
        # Update state
        updated_state = state.copy()
        updated_state["quality_scores"]["overall"] = overall_quality
        updated_state["metadata"]["quality_gate_result"] = {
            "overall_score": overall_quality,
            "all_passed": all_passed,
            "team_results": quality_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine next action
        if all_passed and overall_quality >= 4.0:
            updated_state["current_step"] = "final_synthesis"
            await self.agui_broadcaster.broadcast_agent_message(
                task_id=task_id,
                agent_id="quality_gate",
                content=f"✅ Quality gate passed! Overall score: {overall_quality:.1f}/5.0",
                streaming=False
            )
        else:
            updated_state["current_step"] = "revision_needed"
            updated_state["human_intervention_required"] = True
            await self.agui_broadcaster.broadcast_agent_message(
                task_id=task_id,
                agent_id="quality_gate",
                content=f"⚠️ Quality gate failed. Score: {overall_quality:.1f}/5.0. Human review required.",
                streaming=False
            )
        
        return updated_state
    
    async def _human_approval_node(self, state: ATLASState) -> ATLASState:
        """Human approval node with comprehensive review"""
        
        task_id = state["task_id"]
        
        # Broadcast human review required
        await self.agui_broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="human_reviewer",
            status="waiting",
            details="Human review and approval required"
        )
        
        # Prepare review package
        review_package = {
            "task_summary": {
                "description": state["task_description"],
                "type": state["task_type"],
                "priority": state["task_priority"]
            },
            "team_results": state["team_results"],
            "quality_scores": state["quality_scores"],
            "performance_metrics": state["performance_metrics"],
            "cost_summary": state["cost_tracking"],
            "error_log": state["error_log"],
            "recommendations": self._generate_review_recommendations(state)
        }
        
        # Broadcast review package
        await self.agui_broadcaster.broadcast_system_message(
            task_id=task_id,
            message="Human review package prepared",
            data=review_package
        )
        
        # Update state for human review
        updated_state = state.copy()
        updated_state["workflow_stage"] = "human_review"
        updated_state["approval_status"] = "pending"
        updated_state["human_intervention_required"] = True
        updated_state["checkpoint_data"]["human_review"] = {
            "timestamp": datetime.now().isoformat(),
            "review_package": review_package
        }
        
        return updated_state
    
    async def _final_synthesis_node(self, state: ATLASState) -> ATLASState:
        """Final synthesis and output generation"""
        
        task_id = state["task_id"]
        
        # Create synthesis agent
        synthesis_agent_id = await self.agent_manager.create_fresh_agent(
            config=AgentConfig(
                agent_id="synthesis_agent",
                agent_type="specialist",
                team="synthesis",
                model_provider="anthropic",
                model_name="claude-3-opus",
                tools=["document_generation", "synthesis_tools", "export_tools"],
                persona_file="personas/synthesis_agent.md"
            ),
            task_id=task_id,
            specialized_role="final_synthesis"
        )
        
        try:
            # Broadcast synthesis start
            await self.agui_broadcaster.broadcast_agent_status(
                task_id=task_id,
                agent_id=synthesis_agent_id,
                status="synthesizing",
                details="Creating final comprehensive output"
            )
            
            # Prepare all results for synthesis
            synthesis_input = {
                "task_description": state["task_description"],
                "team_results": state["team_results"],
                "quality_scores": state["quality_scores"],
                "user_inputs": state["user_inputs"],
                "global_context": state["global_context"],
                "performance_summary": self._generate_performance_summary(state)
            }
            
            # Execute final synthesis
            final_output = await self.agent_manager.execute_agent_task(
                agent_id=synthesis_agent_id,
                task_data={
                    "role": "Create comprehensive final output synthesis",
                    "synthesis_input": synthesis_input,
                    "output_requirements": {
                        "format": "comprehensive_report",
                        "include_executive_summary": True,
                        "include_methodology": True,
                        "include_recommendations": True,
                        "include_appendices": True
                    }
                }
            )
            
            # Update state with final output
            updated_state = state.copy()
            updated_state["final_output"] = final_output
            updated_state["workflow_stage"] = "completed"
            updated_state["current_step"] = "end"
            updated_state["updated_at"] = datetime.now().isoformat()
            
            # Final checkpoint
            updated_state["checkpoint_data"]["final_synthesis"] = {
                "timestamp": datetime.now().isoformat(),
                "output_quality": final_output.get("quality_score", 0),
                "synthesis_complete": True
            }
            
            # Broadcast completion
            await self.agui_broadcaster.broadcast_task_completion(
                task_id=task_id,
                result=final_output
            )
            
            return updated_state
            
        finally:
            await self.agent_manager.cleanup_agent(synthesis_agent_id, preserve_learnings=True)
    
    # Routing Functions
    def _route_from_supervisor(self, state: ATLASState) -> str:
        """Route from global supervisor based on current state"""
        current_step = state.get("current_step", "start")
        completed_teams = state.get("completed_teams", [])
        
        # Check for errors
        if state.get("error_log") and state["retry_count"].get(current_step, 0) >= 3:
            return "error_recovery"
        
        # Check for human intervention
        if state.get("human_intervention_required"):
            return "human_approval"
        
        # Normal workflow routing
        if current_step == "research" and "research" not in completed_teams:
            return "research"
        elif current_step == "analysis" and "analysis" not in completed_teams:
            return "analysis"
        elif current_step == "writing" and "writing" not in completed_teams:
            return "writing"
        elif current_step == "rating" and "rating" not in completed_teams:
            return "rating"
        elif len(completed_teams) >= 3:  # At least 3 teams completed
            return "quality_gate"
        elif current_step == "final_synthesis":
            return "final_synthesis"
        else:
            return "end"
    
    def _route_after_team_completion(self, state: ATLASState) -> str:
        """Route after team completion"""
        # Check quality of just completed team
        last_completed = state["completed_teams"][-1] if state["completed_teams"] else ""
        
        if last_completed and last_completed in state["quality_scores"]:
            quality_score = state["quality_scores"][last_completed]
            if quality_score < 3.0:  # Poor quality
                return "error_recovery"
            elif quality_score < 4.0:  # Moderate quality
                return "human_approval"
        
        return "continue"
    
    def _route_from_quality_gate(self, state: ATLASState) -> str:
        """Route from quality gate"""
        current_step = state.get("current_step", "")
        
        if current_step == "final_synthesis":
            return "final_synthesis"
        elif current_step == "revision_needed":
            return "human_review"
        else:
            return "approved"
    
    def _route_from_human_approval(self, state: ATLASState) -> str:
        """Route from human approval"""
        approval_status = state.get("approval_status", "pending")
        
        if approval_status == "approved":
            return "approved"
        elif approval_status == "rejected":
            return "rejected"
        else:
            return "modifications"
    
    def _route_from_error_recovery(self, state: ATLASState) -> str:
        """Route from error recovery"""
        # Implement error recovery logic
        error_count = len(state.get("error_log", []))
        
        if error_count < 3:
            return "retry"
        elif error_count < 5:
            return "escalate"
        else:
            return "abort"
    
    # Helper Methods
    def _prepare_supervisor_context(self, state: ATLASState) -> Dict[str, Any]:
        """Prepare comprehensive context for supervisor decision making"""
        return {
            "task_progress": {
                "completed_teams": state.get("completed_teams", []),
                "current_step": state.get("current_step", ""),
                "workflow_stage": state.get("workflow_stage", "")
            },
            "quality_status": state.get("quality_scores", {}),
            "resource_usage": {
                "cost_tracking": state.get("cost_tracking", {}),
                "performance_metrics": state.get("performance_metrics", {})
            },
            "error_status": {
                "error_count": len(state.get("error_log", [])),
                "retry_counts": state.get("retry_count", {}),
                "escalations": state.get("escalations", [])
            },
            "user_context": {
                "inputs": state.get("user_inputs", []),
                "priority": state.get("task_priority", "normal")
            }
        }
    
    def _get_available_options(self, state: ATLASState) -> List[str]:
        """Get available options for supervisor"""
        completed = set(state.get("completed_teams", []))
        all_teams = {"research", "analysis", "writing", "rating"}
        remaining = all_teams - completed
        
        options = list(remaining)
        
        if len(completed) >= 3:
            options.append("quality_gate")
        
        if state.get("error_log"):
            options.append("error_recovery")
        
        if any(score < 4.0 for score in state.get("quality_scores", {}).values()):
            options.append("human_approval")
        
        if len(completed) == len(all_teams):
            options.append("final_synthesis")
        
        return options
    
    def _get_team_objective(self, team_name: str, task_data: ATLASState) -> str:
        """Get specific objective for each team"""
        objectives = {
            "research": f"Gather comprehensive information about: {task_data['task_description']}",
            "analysis": f"Analyze and interpret research findings for: {task_data['task_description']}",
            "writing": f"Create clear, structured content based on analysis of: {task_data['task_description']}",
            "rating": f"Evaluate quality and provide feedback on work for: {task_data['task_description']}"
        }
        return objectives.get(team_name, f"Complete {team_name} work for: {task_data['task_description']}")
    
    def _generate_performance_summary(self, state: ATLASState) -> Dict[str, Any]:
        """Generate comprehensive performance summary"""
        return {
            "total_execution_time": sum(
                time for key, time in state.get("performance_metrics", {}).items()
                if "execution_time" in key
            ),
            "total_cost": sum(state.get("cost_tracking", {}).values()),
            "average_quality": sum(state.get("quality_scores", {}).values()) / len(state.get("quality_scores", {})) if state.get("quality_scores") else 0,
            "teams_completed": len(state.get("completed_teams", [])),
            "error_count": len(state.get("error_log", [])),
            "human_interventions": len(state.get("escalations", []))
        }
    
    def _generate_review_recommendations(self, state: ATLASState) -> List[str]:
        """Generate recommendations for human review"""
        recommendations = []
        
        # Quality-based recommendations
        for team, score in state.get("quality_scores", {}).items():
            if score < 4.0:
                recommendations.append(f"Consider revising {team} work (score: {score:.1f}/5.0)")
        
        # Cost-based recommendations
        total_cost = sum(state.get("cost_tracking", {}).values())
        if total_cost > 10.0:
            recommendations.append(f"High cost detected: ${total_cost:.2f}")
        
        # Error-based recommendations
        error_count = len(state.get("error_log", []))
        if error_count > 2:
            recommendations.append(f"Multiple errors occurred ({error_count})")
        
        return recommendations
    
    async def execute_workflow(
        self, 
        initial_state: ATLASState,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute complete ATLAS workflow"""
        
        task_id = initial_state["task_id"]
        
        try:
            # Execute workflow with checkpointing
            final_state = await self.workflow_graph.ainvoke(
                initial_state,
                config={
                    "configurable": {"thread_id": task_id},
                    **(config or {})
                }
            )
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            
            # Broadcast error
            await self.agui_broadcaster.broadcast_error(
                task_id=task_id,
                error_message=str(e),
                error_type="workflow_execution"
            )
            
            raise
    
    async def resume_workflow(
        self,
        task_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resume workflow from checkpoint"""
        
        try:
            # Resume from latest checkpoint
            final_state = await self.workflow_graph.ainvoke(
                None,  # State will be loaded from checkpoint
                config={
                    "configurable": {"thread_id": task_id},
                    **(config or {})
                }
            )
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow resume error: {e}")
            raise

# Example usage
async def main():
    from agent_manager import ATLASAgentManager
    from ag_ui_integration import ATLASAGUIBroadcaster
    
    # Initialize components
    agent_manager = ATLASAgentManager()
    agui_broadcaster = ATLASAGUIBroadcaster()
    workflow_config = WorkflowConfig()
    
    # Create LangGraph workflow
    workflow = ATLASLangGraphWorkflow(
        postgres_url="postgresql://user:pass@localhost:5432/atlas",
        agent_manager=agent_manager,
        agui_broadcaster=agui_broadcaster,
        workflow_config=workflow_config
    )
    
    # Create initial state
    initial_state = ATLASState(
        task_id="task_123",
        task_description="Analyze market opportunities for AI-powered customer service",
        task_type="strategic_analysis",
        task_priority="high",
        user_id="user_456",
        current_step="start",
        workflow_stage="initialization",
        completed_teams=[],
        active_agents=[],
        team_results={},
        global_context={},
        shared_knowledge={},
        user_inputs=[],
        quality_scores={},
        performance_metrics={},
        cost_tracking={},
        error_log=[],
        retry_count={},
        escalations=[],
        human_intervention_required=False,
        approval_status=None,
        checkpoint_data={},
        intermediate_outputs={},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        metadata={}
    )
    
    # Execute workflow
    result = await workflow.execute_workflow(initial_state)
    print(f"Workflow completed: {result['final_output']}")

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive LangGraph guide provides the foundation for sophisticated multi-agent orchestration in the ATLAS system, leveraging the latest 2025 features for stateful execution, advanced checkpoint management, error recovery, and production-ready deployment.