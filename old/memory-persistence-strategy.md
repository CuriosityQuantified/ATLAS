# ATLAS Memory Persistence & Context Engineering Strategy

## Memory Type Taxonomy

### 1. Working Memory (Context Window)
**Duration**: Current task/session only  
**Location**: In-memory (agent state)  
**Size Limit**: 30,000 tokens max, summarized to 20,000 + recent messages  
**Purpose**: Active task execution, immediate context

### 2. Short-Term Memory (Session Cache)
**Duration**: 24-72 hours  
**Location**: Redis cache + ChromaDB  
**Purpose**: Recent interactions, temporary task state, quick recall

### 3. Episodic Memory (Project-Based)
**Duration**: Project lifetime + 30 days  
**Location**: ChromaDB with project namespacing  
**Purpose**: Project-specific knowledge, task history, outcomes

### 4. Long-Term Memory (System Knowledge)
**Duration**: Permanent (with versioning)  
**Location**: ChromaDB shared collections  
**Purpose**: Learned patterns, best practices, domain knowledge

### 5. Procedural Memory (Skills & Workflows)
**Duration**: Permanent with updates  
**Location**: ChromaDB + code repositories  
**Purpose**: How-to knowledge, successful strategies, tool usage

## Context Engineering Implementation

### Working Memory Management

```python
from typing import List, Dict, Optional, Tuple
import tiktoken
from datetime import datetime
import json

class WorkingMemoryManager:
    def __init__(self, max_tokens: int = 30000, summary_target: int = 20000):
        self.max_tokens = max_tokens
        self.summary_target = summary_target
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        
    def manage_context(
        self,
        messages: List[Dict[str, str]],
        agent_type: str = "worker"
    ) -> List[Dict[str, str]]:
        """Manage context window based on agent type"""
        
        # Supervisor agents get full context
        if agent_type in ["global_supervisor", "team_supervisor"]:
            return self._manage_supervisor_context(messages)
        
        # Worker agents get engineered context
        return self._manage_worker_context(messages)
    
    def _manage_supervisor_context(
        self,
        messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Supervisors get appropriately summarized full history"""
        total_tokens = self._count_tokens(messages)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # Find split point for summary
        split_point = self._find_summary_split(messages)
        
        # Summarize older messages
        to_summarize = messages[:split_point]
        summary = self._create_summary(to_summarize)
        
        # Keep recent messages
        recent = messages[split_point:]
        
        return [
            {"role": "system", "content": "Previous conversation summary:"},
            {"role": "assistant", "content": summary},
            {"role": "system", "content": "Recent messages:"}
        ] + recent
    
    def _manage_worker_context(
        self,
        messages: List[Dict[str, str]],
        task_context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Workers get task-specific engineered context"""
        # Start with task context from supervisor
        if task_context:
            context = [
                {"role": "system", "content": "Task context from supervisor:"},
                {"role": "system", "content": task_context}
            ]
        else:
            context = []
        
        # Add only relevant recent messages
        relevant_messages = self._filter_relevant_messages(messages[-10:])
        
        return context + relevant_messages
    
    def _count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count total tokens in messages"""
        total = 0
        for msg in messages:
            total += len(self.encoder.encode(msg.get("content", "")))
        return total
    
    def _find_summary_split(self, messages: List[Dict[str, str]]) -> int:
        """Find optimal split point for summarization"""
        target_recent_tokens = self.max_tokens - self.summary_target
        token_count = 0
        
        for i in range(len(messages) - 1, -1, -1):
            token_count += len(self.encoder.encode(messages[i].get("content", "")))
            if token_count >= target_recent_tokens:
                return i + 1
        
        return len(messages) // 2
    
    def _create_summary(self, messages: List[Dict[str, str]]) -> str:
        """Create intelligent summary of messages"""
        # This would use an LLM to create a smart summary
        # For now, returning a placeholder
        return f"Summary of {len(messages)} messages covering key decisions, findings, and context."
    
    def _filter_relevant_messages(
        self,
        messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Filter messages relevant to current task"""
        # Implementation would analyze message relevance
        return messages
```

### Memory Persistence Strategies

```python
from enum import Enum
from datetime import datetime, timedelta
import asyncio

class MemoryType(Enum):
    WORKING = "working"
    SHORT_TERM = "short_term"
    EPISODIC = "episodic"
    LONG_TERM = "long_term"
    PROCEDURAL = "procedural"

class MemoryPersistenceManager:
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.retention_policies = {
            MemoryType.WORKING: timedelta(hours=0),  # Session only
            MemoryType.SHORT_TERM: timedelta(days=3),
            MemoryType.EPISODIC: timedelta(days=30),  # + project lifetime
            MemoryType.LONG_TERM: None,  # Permanent
            MemoryType.PROCEDURAL: None  # Permanent with versioning
        }
    
    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Dict[str, any],
        project_id: Optional[str] = None
    ) -> str:
        """Store memory with appropriate persistence"""
        
        # Add persistence metadata
        metadata.update({
            "memory_type": memory_type.value,
            "created_at": datetime.now().isoformat(),
            "expires_at": self._calculate_expiry(memory_type, project_id),
            "project_id": project_id,
            "version": 1
        })
        
        # Route to appropriate storage
        if memory_type == MemoryType.WORKING:
            return await self._store_working_memory(content, metadata)
        elif memory_type == MemoryType.SHORT_TERM:
            return await self._store_short_term(content, metadata)
        elif memory_type == MemoryType.EPISODIC:
            return await self._store_episodic(content, metadata, project_id)
        elif memory_type == MemoryType.LONG_TERM:
            return await self._store_long_term(content, metadata)
        elif memory_type == MemoryType.PROCEDURAL:
            return await self._store_procedural(content, metadata)
    
    def _calculate_expiry(
        self,
        memory_type: MemoryType,
        project_id: Optional[str] = None
    ) -> Optional[str]:
        """Calculate expiry date based on memory type"""
        retention = self.retention_policies[memory_type]
        
        if retention is None:
            return None
        
        if memory_type == MemoryType.EPISODIC and project_id:
            # Check project status to extend retention
            project_active = self._is_project_active(project_id)
            if project_active:
                return None  # No expiry while project active
        
        expiry = datetime.now() + retention
        return expiry.isoformat()
    
    async def _store_working_memory(
        self,
        content: str,
        metadata: Dict
    ) -> str:
        """Store in Redis for fast access"""
        # Implementation for Redis storage
        pass
    
    async def _store_long_term(
        self,
        content: str,
        metadata: Dict
    ) -> str:
        """Store with quality checks and deduplication"""
        # Check for duplicates
        similar = await self.memory.retrieve_memories(
            query=content[:200],
            memory_type="shared",
            n_results=3
        )
        
        # If highly similar memory exists, update instead
        for mem in similar:
            if mem['distance'] < 0.1:  # Very similar
                return await self._update_memory(mem['id'], content, metadata)
        
        # Store new memory
        return self.memory.store_memory(
            content=content,
            memory_type="shared",
            metadata=metadata
        )
```

### Context Engineering for Different Agents

```python
class SupervisorContextEngineer:
    """Context engineering for supervisor agents"""
    
    def prepare_context(
        self,
        task: Dict,
        team_status: Dict,
        memory_recall: List[Dict]
    ) -> str:
        """Prepare context for supervisor decision making"""
        
        context_template = """
        ## Current Task
        {task_description}
        
        ## Team Status
        - Research Team: {research_status}
        - Analysis Team: {analysis_status}
        - Writing Team: {writing_status}
        - Rating Team: {rating_status}
        
        ## Relevant Prior Experience
        {memory_insights}
        
        ## Available Actions
        - Assign subtasks to teams
        - Request revisions
        - Escalate issues
        - Approve outputs
        """
        
        memory_insights = self._synthesize_memories(memory_recall)
        
        return context_template.format(
            task_description=task['description'],
            research_status=team_status.get('research', 'idle'),
            analysis_status=team_status.get('analysis', 'idle'),
            writing_status=team_status.get('writing', 'idle'),
            rating_status=team_status.get('rating', 'idle'),
            memory_insights=memory_insights
        )
    
    def _synthesize_memories(self, memories: List[Dict]) -> str:
        """Synthesize relevant memories into insights"""
        if not memories:
            return "No relevant prior experience found."
        
        insights = []
        for mem in memories[:5]:  # Top 5 most relevant
            insights.append(f"- {mem['content'][:100]}...")
        
        return "\n".join(insights)

class WorkerContextEngineer:
    """Context engineering for worker agents"""
    
    def prepare_context(
        self,
        task: Dict,
        supervisor_guidance: str,
        team_knowledge: List[Dict],
        tools_available: List[str]
    ) -> str:
        """Prepare focused context for worker execution"""
        
        context_template = """
        ## Your Task
        {task_description}
        
        ## Supervisor Guidance
        {supervisor_guidance}
        
        ## Relevant Team Knowledge
        {team_knowledge}
        
        ## Available Tools
        {tools_list}
        
        ## Expected Output Format
        {output_format}
        """
        
        return context_template.format(
            task_description=task['description'],
            supervisor_guidance=supervisor_guidance,
            team_knowledge=self._format_team_knowledge(team_knowledge),
            tools_list="\n".join(f"- {tool}" for tool in tools_available),
            output_format=task.get('output_format', 'Structured findings')
        )
```

## Memory Lifecycle Management

### 1. Memory Promotion Pipeline
```python
async def promote_memories():
    """Promote valuable short-term memories to long-term"""
    # Run daily
    short_term_memories = await get_high_value_short_term()
    
    for memory in short_term_memories:
        if memory['usage_count'] > 5 or memory['importance'] == 'high':
            await promote_to_long_term(memory)
```

### 2. Memory Consolidation
```python
async def consolidate_memories():
    """Merge similar memories and update knowledge"""
    # Run weekly
    clusters = await cluster_similar_memories()
    
    for cluster in clusters:
        consolidated = await create_consolidated_memory(cluster)
        await store_as_long_term(consolidated)
        await archive_originals(cluster)
```

### 3. Memory Garbage Collection
```python
async def cleanup_expired_memories():
    """Remove expired memories based on retention policies"""
    # Run daily
    expired = await find_expired_memories()
    
    for memory in expired:
        if memory['type'] == 'episodic':
            # Check if project still active
            if not is_project_active(memory['project_id']):
                await archive_memory(memory)
        else:
            await delete_memory(memory)
```

## Configuration

```yaml
# memory-config.yaml
memory:
  working:
    max_tokens: 30000
    summary_target: 20000
    recent_messages_count: 4
  
  short_term:
    ttl_hours: 72
    storage: redis
    backup_to_chromadb: true
  
  episodic:
    base_ttl_days: 30
    project_extension: true
    namespace_by_project: true
  
  long_term:
    deduplication_threshold: 0.1
    quality_threshold: 0.7
    require_validation: true
  
  procedural:
    version_control: true
    max_versions: 10
    approval_required: true

context_engineering:
  supervisor:
    include_full_history: true
    summarization_model: "gpt-4-turbo"
    max_context_window: 128000
  
  worker:
    include_task_only: true
    max_context_window: 8000
    relevant_memories_count: 5
```

This architecture ensures that:
1. **System knowledge** accumulates permanently to improve performance
2. **Project memories** persist appropriately with their lifecycle
3. **Context windows** are managed intelligently based on agent roles
4. **Supervisors** maintain oversight with summarized full context
5. **Workers** receive focused, task-specific context from their supervisors