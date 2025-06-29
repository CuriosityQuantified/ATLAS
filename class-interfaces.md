# ATLAS Class Interfaces & API Specifications

## Core Agent Interfaces

### Base Agent Interface
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

class AgentStatus(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"
    TERMINATED = "terminated"

class TaskComplexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TaskContext:
    task_id: str
    user_id: str
    task_type: str
    complexity: TaskComplexity
    priority: int
    deadline: Optional[datetime] = None
    parent_task_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class AgentResult:
    agent_id: str
    task_id: str
    status: str
    result_data: Dict[str, Any]
    execution_time: float
    tokens_used: int
    cost: float
    quality_score: float
    error_count: int = 0
    errors: List[str] = None
    created_at: datetime = None

class BaseAgent(ABC):
    """Foundation interface for all ATLAS agents"""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        config: Dict[str, Any],
        letta_client: 'LettaClient',
        tools: List[str],
        memory_access: 'MemoryAccess'
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.letta_client = letta_client
        self.tools = tools
        self.memory_access = memory_access
        self.status = AgentStatus.INITIALIZING
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
    
    @abstractmethod
    async def initialize(self, context: TaskContext) -> bool:
        """Initialize agent for specific task context"""
        pass
    
    @abstractmethod
    async def execute_task(
        self, 
        task: Dict[str, Any], 
        context: TaskContext
    ) -> AgentResult:
        """Execute assigned task with full context"""
        pass
    
    @abstractmethod
    async def handle_error(
        self, 
        error: Exception, 
        context: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Handle errors with contextual recovery strategies"""
        pass
    
    async def escalate(
        self, 
        reason: str, 
        context: Dict[str, Any],
        escalation_type: str = "standard"
    ) -> Dict[str, Any]:
        """Escalate to next level in hierarchy"""
        escalation_data = {
            'agent_id': self.agent_id,
            'reason': reason,
            'context': context,
            'escalation_type': escalation_type,
            'timestamp': datetime.now().isoformat()
        }
        return await self._send_escalation(escalation_data)
    
    @abstractmethod
    async def _send_escalation(self, escalation_data: Dict) -> Dict[str, Any]:
        """Implementation-specific escalation logic"""
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'tools_available': len(self.tools)
        }
    
    async def cleanup(self, preserve_learnings: bool = True) -> Dict[str, Any]:
        """Clean up agent resources"""
        cleanup_result = {
            'agent_id': self.agent_id,
            'cleanup_time': datetime.now().isoformat(),
            'learnings_preserved': preserve_learnings
        }
        
        if preserve_learnings:
            learnings = await self._extract_learnings()
            cleanup_result['learnings_extracted'] = len(learnings)
        
        self.status = AgentStatus.TERMINATED
        return cleanup_result
    
    @abstractmethod
    async def _extract_learnings(self) -> List[Dict[str, Any]]:
        """Extract learnings from agent for preservation"""
        pass

class SupervisorAgent(BaseAgent):
    """Team supervisor with worker coordination capabilities"""
    
    def __init__(
        self,
        team_name: str,
        worker_agent_types: List[str],
        coordination_strategy: str = "intelligent",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.team_name = team_name
        self.worker_agent_types = worker_agent_types
        self.coordination_strategy = coordination_strategy
        self.active_workers: Dict[str, str] = {}  # worker_id -> agent_id
        self.task_queue: List[Dict] = []
        self.results_cache: Dict[str, AgentResult] = {}
    
    @abstractmethod
    async def coordinate_team(
        self, 
        task: Dict[str, Any], 
        context: TaskContext
    ) -> Dict[str, Any]:
        """Coordinate team of workers for complex task"""
        pass
    
    async def assign_subtask(
        self,
        worker_type: str,
        subtask: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """Assign subtask to specific worker type"""
        subtask_id = f"subtask_{uuid.uuid4()}"
        
        assignment = {
            'subtask_id': subtask_id,
            'worker_type': worker_type,
            'task_data': subtask,
            'priority': priority,
            'assigned_at': datetime.now().isoformat(),
            'status': 'assigned'
        }
        
        self.task_queue.append(assignment)
        return subtask_id
    
    async def collect_worker_results(
        self, 
        timeout: int = 300
    ) -> Dict[str, AgentResult]:
        """Collect results from all active workers"""
        results = {}
        
        for worker_id, agent_id in self.active_workers.items():
            try:
                result = await self._get_worker_result(agent_id, timeout)
                results[worker_id] = result
            except asyncio.TimeoutError:
                results[worker_id] = AgentResult(
                    agent_id=agent_id,
                    task_id="timeout",
                    status="timeout",
                    result_data={'error': 'Worker timeout'},
                    execution_time=timeout,
                    tokens_used=0,
                    cost=0,
                    quality_score=0,
                    error_count=1
                )
        
        return results
    
    @abstractmethod
    async def _get_worker_result(
        self, 
        agent_id: str, 
        timeout: int
    ) -> AgentResult:
        """Get result from specific worker"""
        pass
    
    async def synthesize_team_results(
        self, 
        worker_results: Dict[str, AgentResult],
        synthesis_strategy: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Synthesize results from multiple workers"""
        synthesis_prompt = self._build_synthesis_prompt(
            worker_results, synthesis_strategy
        )
        
        synthesis_result = await self.letta_client.send_message(
            agent_id=self.agent_id,
            message=synthesis_prompt,
            role="user"
        )
        
        return {
            'synthesis': synthesis_result.messages[-1].text,
            'worker_count': len(worker_results),
            'strategy': synthesis_strategy,
            'quality_scores': [r.quality_score for r in worker_results.values()],
            'total_cost': sum(r.cost for r in worker_results.values()),
            'total_tokens': sum(r.tokens_used for r in worker_results.values())
        }
    
    @abstractmethod
    def _build_synthesis_prompt(
        self, 
        results: Dict[str, AgentResult], 
        strategy: str
    ) -> str:
        """Build prompt for result synthesis"""
        pass

class WorkerAgent(BaseAgent):
    """Specialized worker with domain-specific capabilities"""
    
    def __init__(
        self,
        specialization: str,
        expertise_areas: List[str],
        performance_targets: Dict[str, float],
        **kwargs
    ):
        super().__init__(**kwargs)
        self.specialization = specialization
        self.expertise_areas = expertise_areas
        self.performance_targets = performance_targets
        self.current_task: Optional[Dict] = None
        self.performance_history: List[Dict] = []
    
    async def execute_specialized_task(
        self,
        task: Dict[str, Any],
        context: TaskContext,
        specialization_params: Dict[str, Any] = None
    ) -> AgentResult:
        """Execute task using specialized capabilities"""
        
        start_time = time.time()
        self.current_task = task
        self.status = AgentStatus.EXECUTING
        
        try:
            # Apply specialization-specific processing
            processed_task = await self._apply_specialization(
                task, specialization_params
            )
            
            # Execute with domain expertise
            result = await self._execute_with_expertise(
                processed_task, context
            )
            
            # Track performance
            execution_time = time.time() - start_time
            performance_data = await self._calculate_performance_metrics(
                result, execution_time
            )
            
            self.performance_history.append(performance_data)
            self.status = AgentStatus.COMPLETED
            
            return AgentResult(
                agent_id=self.agent_id,
                task_id=context.task_id,
                status="completed",
                result_data=result,
                execution_time=execution_time,
                tokens_used=performance_data['tokens_used'],
                cost=performance_data['cost'],
                quality_score=performance_data['quality_score']
            )
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            error_result = await self.handle_error(e, {'task': task, 'context': context})
            
            return AgentResult(
                agent_id=self.agent_id,
                task_id=context.task_id,
                status="error",
                result_data=error_result,
                execution_time=time.time() - start_time,
                tokens_used=0,
                cost=0,
                quality_score=0,
                error_count=1,
                errors=[str(e)]
            )
    
    @abstractmethod
    async def _apply_specialization(
        self, 
        task: Dict[str, Any], 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply specialization-specific task processing"""
        pass
    
    @abstractmethod
    async def _execute_with_expertise(
        self, 
        task: Dict[str, Any], 
        context: TaskContext
    ) -> Dict[str, Any]:
        """Execute task using domain expertise"""
        pass
    
    async def _calculate_performance_metrics(
        self, 
        result: Dict[str, Any], 
        execution_time: float
    ) -> Dict[str, Any]:
        """Calculate performance metrics for this execution"""
        return {
            'execution_time': execution_time,
            'tokens_used': result.get('tokens_used', 0),
            'cost': result.get('cost', 0),
            'quality_score': await self._assess_result_quality(result),
            'target_met': execution_time <= self.performance_targets.get('max_time', float('inf'))
        }
    
    @abstractmethod
    async def _assess_result_quality(self, result: Dict[str, Any]) -> float:
        """Assess quality of work result"""
        pass
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for this worker"""
        if not self.performance_history:
            return {'status': 'no_data'}
        
        return {
            'total_tasks': len(self.performance_history),
            'avg_execution_time': sum(p['execution_time'] for p in self.performance_history) / len(self.performance_history),
            'avg_quality_score': sum(p['quality_score'] for p in self.performance_history) / len(self.performance_history),
            'total_cost': sum(p['cost'] for p in self.performance_history),
            'targets_met': sum(1 for p in self.performance_history if p['target_met']),
            'specialization': self.specialization,
            'expertise_areas': self.expertise_areas
        }
```

## Memory Management Interfaces

```python
class MemoryType(Enum):
    WORKING = "working"
    SHORT_TERM = "short_term"
    EPISODIC = "episodic"
    LONG_TERM = "long_term"
    PROCEDURAL = "procedural"
    SYSTEM = "system"

@dataclass
class MemoryItem:
    memory_id: str
    content: str
    memory_type: MemoryType
    confidence: float
    created_at: datetime
    agent_id: str
    task_id: str
    metadata: Dict[str, Any]
    embeddings: Optional[List[float]] = None
    relationships: List[str] = None

class MemoryAccess(ABC):
    """Interface for agent memory access"""
    
    @abstractmethod
    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        confidence: float,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store memory item and return memory_id"""
        pass
    
    @abstractmethod
    async def retrieve_memories(
        self,
        query: str,
        memory_types: List[MemoryType] = None,
        limit: int = 10,
        min_confidence: float = 0.5
    ) -> List[MemoryItem]:
        """Retrieve relevant memories based on query"""
        pass
    
    @abstractmethod
    async def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing memory item"""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory item"""
        pass
    
    async def search_semantic(
        self,
        query: str,
        memory_types: List[MemoryType] = None,
        similarity_threshold: float = 0.7
    ) -> List[MemoryItem]:
        """Semantic search across memories"""
        pass

class UnifiedMemoryManager:
    """Manages all memory types across multiple storage systems"""
    
    def __init__(
        self,
        postgres_manager: 'PostgreSQLManager',
        chromadb_manager: 'ChromaDBManager',
        neo4j_manager: 'Neo4jManager',
        redis_manager: 'RedisManager',
        minio_manager: 'MinIOManager'
    ):
        self.postgres = postgres_manager
        self.chromadb = chromadb_manager
        self.neo4j = neo4j_manager
        self.redis = redis_manager
        self.minio = minio_manager
        self.memory_routers = self._setup_memory_routers()
    
    async def create_agent_memory_context(
        self,
        agent_type: str,
        task_context: TaskContext
    ) -> 'AgentMemoryContext':
        """Create memory context for new agent"""
        
        # Get relevant long-term memories
        relevant_memories = await self.chromadb.search_relevant_memories(
            query=task_context.task_type,
            agent_type=agent_type,
            limit=10
        )
        
        # Get related knowledge from graph
        related_knowledge = await self.neo4j.find_related_concepts(
            concept=task_context.task_type,
            max_depth=2
        )
        
        # Create memory context
        memory_context = AgentMemoryContext(
            agent_type=agent_type,
            task_context=task_context,
            relevant_memories=relevant_memories,
            related_knowledge=related_knowledge,
            working_memory_limit=self._get_working_memory_limit(agent_type)
        )
        
        return memory_context
    
    async def capture_agent_learnings(
        self,
        agent_id: str,
        agent_type: str,
        task_result: AgentResult
    ) -> Dict[str, Any]:
        """Capture and process learnings from completed agent"""
        
        # Extract conversation history from Letta
        conversation_history = await self._get_letta_conversation(agent_id)
        
        # Analyze learnings
        learning_analysis = await self._analyze_learnings(
            conversation_history,
            task_result,
            agent_type
        )
        
        # Store high-quality learnings
        if learning_analysis['quality_score'] >= 4.0:
            await self._store_validated_learnings(learning_analysis)
        
        return learning_analysis
    
    @abstractmethod
    async def _analyze_learnings(
        self,
        conversation: List[Dict],
        result: AgentResult,
        agent_type: str
    ) -> Dict[str, Any]:
        """Analyze agent conversation for learnings"""
        pass
    
    async def _store_validated_learnings(
        self,
        learning_data: Dict[str, Any]
    ):
        """Store validated learnings across storage systems"""
        
        # Store in vector database for semantic search
        vector_id = await self.chromadb.store_agent_memory(
            agent_type=learning_data['agent_type'],
            content=learning_data['summary'],
            task_context=learning_data['task_context'],
            confidence=learning_data['confidence']
        )
        
        # Store in knowledge graph for relationships
        graph_node_id = await self.neo4j.create_knowledge_node(
            knowledge_type='agent_learning',
            content=learning_data,
            source_info={
                'agent_id': learning_data['agent_id'],
                'vector_id': vector_id
            }
        )
        
        # Store metadata in PostgreSQL
        await self.postgres.store_learning_metadata(
            learning_data, vector_id, graph_node_id
        )

class AgentMemoryContext:
    """Memory context provided to agents"""
    
    def __init__(
        self,
        agent_type: str,
        task_context: TaskContext,
        relevant_memories: List[MemoryItem],
        related_knowledge: List[Dict],
        working_memory_limit: int
    ):
        self.agent_type = agent_type
        self.task_context = task_context
        self.relevant_memories = relevant_memories
        self.related_knowledge = related_knowledge
        self.working_memory_limit = working_memory_limit
        self.working_memory: List[str] = []
    
    def add_to_working_memory(self, content: str) -> bool:
        """Add content to working memory if space available"""
        if len(self.working_memory) < self.working_memory_limit:
            self.working_memory.append(content)
            return True
        return False
    
    def get_context_summary(self) -> str:
        """Get formatted context summary for agent"""
        context_parts = [
            f"Task: {self.task_context.task_type}",
            f"Relevant Experience: {len(self.relevant_memories)} items",
            f"Related Knowledge: {len(self.related_knowledge)} concepts"
        ]
        
        if self.relevant_memories:
            context_parts.append("Key Past Learnings:")
            for memory in self.relevant_memories[:3]:
                context_parts.append(f"- {memory.content[:100]}...")
        
        return "\n".join(context_parts)
```

## Tool & MCP Interfaces

```python
class ToolResult:
    """Standardized tool execution result"""
    
    def __init__(
        self,
        tool_name: str,
        success: bool,
        result_data: Any,
        execution_time: float,
        cost: float = 0,
        metadata: Dict[str, Any] = None
    ):
        self.tool_name = tool_name
        self.success = success
        self.result_data = result_data
        self.execution_time = execution_time
        self.cost = cost
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class MCPTool(ABC):
    """Base interface for MCP tools"""
    
    def __init__(
        self,
        tool_name: str,
        access_levels: List[str],
        cost_per_execution: float = 0,
        max_concurrent: int = 5
    ):
        self.tool_name = tool_name
        self.access_levels = access_levels
        self.cost_per_execution = cost_per_execution
        self.max_concurrent = max_concurrent
        self.active_executions = 0
    
    @abstractmethod
    async def execute(
        self,
        agent_id: str,
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute tool with given parameters"""
        pass
    
    @abstractmethod
    async def validate_parameters(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate tool parameters"""
        pass
    
    async def check_access(self, agent_id: str, agent_type: str) -> bool:
        """Check if agent has access to this tool"""
        return agent_type in self.access_levels
    
    async def check_capacity(self) -> bool:
        """Check if tool has capacity for new execution"""
        return self.active_executions < self.max_concurrent

class EnhancedWebSearchTool(MCPTool):
    """Enhanced web search with query optimization"""
    
    def __init__(self, **kwargs):
        super().__init__(
            tool_name="enhanced_web_search",
            access_levels=["research_supervisor", "research_worker"],
            **kwargs
        )
    
    async def execute(
        self,
        agent_id: str,
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute enhanced web search"""
        
        start_time = time.time()
        self.active_executions += 1
        
        try:
            # Validate parameters
            validation = await self.validate_parameters(parameters)
            if not validation['valid']:
                return ToolResult(
                    tool_name=self.tool_name,
                    success=False,
                    result_data={'error': validation['error']},
                    execution_time=time.time() - start_time
                )
            
            # Execute multi-step search
            search_result = await self._execute_multi_step_search(
                research_objective=parameters['research_objective'],
                depth=parameters.get('depth', 'comprehensive'),
                context=parameters.get('context')
            )
            
            return ToolResult(
                tool_name=self.tool_name,
                success=True,
                result_data=search_result,
                execution_time=time.time() - start_time,
                cost=self.cost_per_execution
            )
            
        finally:
            self.active_executions -= 1
    
    async def validate_parameters(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate search parameters"""
        required_params = ['research_objective']
        
        for param in required_params:
            if param not in parameters:
                return {
                    'valid': False,
                    'error': f'Missing required parameter: {param}'
                }
        
        return {'valid': True}
    
    @abstractmethod
    async def _execute_multi_step_search(
        self,
        research_objective: str,
        depth: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Implementation of multi-step search logic"""
        pass

class DynamicDebateAgentTool(MCPTool):
    """Creates specialized sub-agents for analysis debates"""
    
    def __init__(self, agent_factory: 'AgentFactory', **kwargs):
        super().__init__(
            tool_name="dynamic_debate_agent",
            access_levels=["analysis_worker", "analysis_supervisor"],
            **kwargs
        )
        self.agent_factory = agent_factory
    
    async def execute(
        self,
        agent_id: str,
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Create and manage analysis debate"""
        
        start_time = time.time()
        debate_agents = []
        
        try:
            # Create debate participants
            participants = await self._create_debate_participants(
                analysis_question=parameters['analysis_question'],
                perspective_count=parameters.get('perspective_count', 5),
                expertise_areas=parameters.get('expertise_areas')
            )
            debate_agents.extend(participants)
            
            # Conduct debate rounds
            debate_history = []
            for round_num in range(parameters.get('debate_rounds', 3)):
                round_result = await self._conduct_debate_round(
                    participants, parameters['analysis_question'], debate_history
                )
                debate_history.append(round_result)
            
            # Synthesize results
            synthesis = await self._synthesize_debate_results(
                parameters['analysis_question'], participants, debate_history
            )
            
            return ToolResult(
                tool_name=self.tool_name,
                success=True,
                result_data={
                    'analysis_question': parameters['analysis_question'],
                    'synthesis': synthesis,
                    'debate_history': debate_history,
                    'participant_count': len(participants)
                },
                execution_time=time.time() - start_time,
                cost=len(participants) * self.cost_per_execution
            )
            
        finally:
            # Clean up debate agents
            for agent in debate_agents:
                await self.agent_factory.cleanup_agent(agent.agent_id)
    
    @abstractmethod
    async def _create_debate_participants(
        self,
        analysis_question: str,
        perspective_count: int,
        expertise_areas: List[str]
    ) -> List[BaseAgent]:
        """Create diverse debate participants"""
        pass

class MCPToolRegistry:
    """Registry for all MCP tools with access control"""
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.access_matrix: Dict[str, List[str]] = {}
        self.usage_tracker = ToolUsageTracker()
    
    def register_tool(
        self,
        tool: MCPTool,
        access_rules: Dict[str, Any] = None
    ):
        """Register tool with access control rules"""
        self.tools[tool.tool_name] = tool
        
        if access_rules:
            self.access_matrix[tool.tool_name] = access_rules.get('allowed_agents', [])
    
    async def execute_tool(
        self,
        tool_name: str,
        agent_id: str,
        agent_type: str,
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute tool with access control and tracking"""
        
        # Check tool exists
        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result_data={'error': f'Tool {tool_name} not found'},
                execution_time=0
            )
        
        tool = self.tools[tool_name]
        
        # Check access
        if not await tool.check_access(agent_id, agent_type):
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result_data={'error': f'Access denied for agent type {agent_type}'},
                execution_time=0
            )
        
        # Check capacity
        if not await tool.check_capacity():
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result_data={'error': 'Tool at capacity, try again later'},
                execution_time=0
            )
        
        # Execute tool
        result = await tool.execute(agent_id, parameters)
        
        # Track usage
        await self.usage_tracker.track_tool_usage(
            tool_name, agent_id, agent_type, result
        )
        
        return result
    
    def get_available_tools(self, agent_type: str) -> List[str]:
        """Get tools available to specific agent type"""
        available = []
        
        for tool_name, tool in self.tools.items():
            if agent_type in tool.access_levels:
                available.append(tool_name)
        
        return available

class ToolUsageTracker:
    """Track tool usage for monitoring and optimization"""
    
    def __init__(self):
        self.usage_history: List[Dict] = []
        self.performance_metrics: Dict[str, Dict] = {}
    
    async def track_tool_usage(
        self,
        tool_name: str,
        agent_id: str,
        agent_type: str,
        result: ToolResult
    ):
        """Track tool usage event"""
        
        usage_event = {
            'tool_name': tool_name,
            'agent_id': agent_id,
            'agent_type': agent_type,
            'success': result.success,
            'execution_time': result.execution_time,
            'cost': result.cost,
            'timestamp': result.timestamp.isoformat()
        }
        
        self.usage_history.append(usage_event)
        
        # Update performance metrics
        if tool_name not in self.performance_metrics:
            self.performance_metrics[tool_name] = {
                'total_uses': 0,
                'successful_uses': 0,
                'total_time': 0,
                'total_cost': 0,
                'avg_execution_time': 0,
                'success_rate': 0
            }
        
        metrics = self.performance_metrics[tool_name]
        metrics['total_uses'] += 1
        if result.success:
            metrics['successful_uses'] += 1
        metrics['total_time'] += result.execution_time
        metrics['total_cost'] += result.cost
        metrics['avg_execution_time'] = metrics['total_time'] / metrics['total_uses']
        metrics['success_rate'] = metrics['successful_uses'] / metrics['total_uses']
    
    def get_tool_performance(self, tool_name: str) -> Dict[str, Any]:
        """Get performance metrics for specific tool"""
        return self.performance_metrics.get(tool_name, {})
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get overall usage summary"""
        total_events = len(self.usage_history)
        successful_events = sum(1 for event in self.usage_history if event['success'])
        
        return {
            'total_tool_executions': total_events,
            'successful_executions': successful_events,
            'overall_success_rate': successful_events / total_events if total_events > 0 else 0,
            'tools_tracked': len(self.performance_metrics),
            'total_cost': sum(event['cost'] for event in self.usage_history)
        }
```

This comprehensive class interface specification provides:

1. **Clear Contracts**: Exact method signatures and expected behaviors
2. **Type Safety**: Full type hints for all parameters and return values
3. **Standardized Results**: Consistent result objects across all components
4. **Error Handling**: Built-in error handling patterns
5. **Performance Tracking**: Metrics collection at every level
6. **Access Control**: Role-based access throughout the system
7. **Resource Management**: Capacity limits and cleanup procedures

These interfaces ensure consistent implementation across all ATLAS components while providing flexibility for specific implementations.