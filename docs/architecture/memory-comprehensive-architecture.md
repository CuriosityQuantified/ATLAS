# ATLAS Memory Comprehensive Architecture

## Overview

ATLAS implements a sophisticated multi-modal memory system that combines persistent memory across multiple database types with fresh-per-task agent creation. This architecture ensures agents have access to long-term learning while being created fresh for each task to maintain consistency and performance.

## Memory Type Taxonomy & Persistence Strategy

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
**Location**: ChromaDB shared collections + Neo4j knowledge graph  
**Purpose**: Learned patterns, best practices, domain knowledge

### 5. Procedural Memory (Skills & Workflows)
**Duration**: Permanent with updates  
**Location**: ChromaDB + Neo4j relationships + code repositories  
**Purpose**: How-to knowledge, successful strategies, tool usage

## Multi-Database Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ATLAS Memory System                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐│
│  │   PostgreSQL    │  │    ChromaDB     │  │   Neo4j     ││
│  │  (Structured)   │  │    (Vector)     │  │   (Graph)   ││
│  │  • Metadata     │  │  • Embeddings   │  │ • Relations ││
│  │  • Projects     │  │  • Semantic     │  │ • Concepts  ││
│  │  • Tasks        │  │  • Similarity   │  │ • Entities  ││
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘│
│           │                     │                    │       │
│  ┌────────┴─────────────────────┴────────────────────┴────┐ │
│  │              Unified Memory Interface                   │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────┴───────────────────────────────┐ │
│  │                  Multi-Modal Storage                    │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │ │
│  │  │   S3/    │ │  File    │ │ Document │ │ Streaming│ │ │
│  │  │  MinIO   │ │  System  │ │   Store  │ │  Store   │ │ │
│  │  │ • Images │ │ • Docs   │ │ • Office │ │ • Audio  │ │ │
│  │  │ • Video  │ │ • Code   │ │ • PDFs   │ │ • Video  │ │ │
│  │  │ • 3D     │ │ • Text   │ │ • PPT    │ │ • Live   │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Database Provider Responsibilities

### PostgreSQL - Primary Operational Database
```python
POSTGRESQL_RESPONSIBILITIES = {
    'agent_configurations': 'Store agent personas, tool access, model preferences',
    'task_metadata': 'Task definitions, status, relationships, checkpoints',
    'user_sessions': 'User interactions, project associations, permissions',
    'system_configuration': 'Global settings, feature flags, deployment config',
    'audit_logs': 'Security events, access logs, change tracking',
    'performance_metrics': 'Agent performance, execution times, error rates',
    'escalation_chains': 'Hierarchy definitions, escalation rules',
    'checkpoint_metadata': 'Checkpoint locations, restoration points, task state'
}
```

### ChromaDB - Vector Embeddings & Semantic Search
```python
CHROMADB_RESPONSIBILITIES = {
    'document_embeddings': 'Semantic search across processed documents',
    'memory_embeddings': 'Agent memory search and context retrieval',
    'task_similarity': 'Find similar past tasks for context',
    'knowledge_search': 'Semantic search across knowledge base',
    'agent_expertise': 'Match agents to tasks based on past performance',
    'content_similarity': 'Duplicate detection and content clustering'
}
```

### Neo4j - Knowledge Graph & Relationships
```python
NEO4J_RESPONSIBILITIES = {
    'concept_relationships': 'Model relationships between concepts and entities',
    'agent_collaboration': 'Track successful agent combinations and patterns',
    'knowledge_provenance': 'Track source and derivation of knowledge',
    'task_dependencies': 'Model complex task interdependencies',
    'learning_paths': 'Track how knowledge builds over time',
    'domain_expertise': 'Map expertise areas and knowledge domains'
}
```

### Redis - Caching & Session Management
```python
REDIS_RESPONSIBILITIES = {
    'session_cache': 'Active user sessions and temporary state',
    'api_response_cache': 'Cache expensive API responses',
    'rate_limiting': 'Track API usage and enforce limits',
    'real_time_coordination': 'Agent coordination and messaging',
    'temporary_results': 'Intermediate task results and working data',
    'model_performance_cache': 'Cache model performance metrics'
}
```

### MinIO/S3 - File Storage & Multi-Modal Content
```python
MINIO_RESPONSIBILITIES = {
    'document_storage': 'Store original documents and processed versions',
    'media_files': 'Audio, video, images from multi-modal interactions',
    'model_artifacts': 'Store fine-tuned models and embeddings',
    'backup_data': 'Database backups and checkpoint files',
    'export_files': 'Generated reports, presentations, exports',
    'temporary_files': 'Large temporary files during processing'
}
```

## Unified Memory Manager Implementation

```python
from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime
import neo4j
import chromadb
import psycopg2
from sqlalchemy import create_engine
from minio import Minio
import redis

class UnifiedMemoryManager:
    """Manages memory across multiple database types"""
    
    def __init__(self, config: Dict[str, Any]):
        # Structured Database (PostgreSQL)
        self.pg_engine = create_engine(config['postgresql_url'])
        
        # Vector Database (ChromaDB)
        self.chroma_client = chromadb.HttpClient(
            host=config['chroma_host'],
            port=config['chroma_port']
        )
        
        # Graph Database (Neo4j)
        self.neo4j_driver = neo4j.GraphDatabase.driver(
            config['neo4j_uri'],
            auth=(config['neo4j_user'], config['neo4j_password'])
        )
        
        # Object Storage (MinIO/S3)
        self.minio_client = Minio(
            config['minio_endpoint'],
            access_key=config['minio_access_key'],
            secret_key=config['minio_secret_key']
        )
        
        # Cache (Redis)
        self.redis_client = redis.Redis(
            host=config['redis_host'],
            port=config['redis_port'],
            decode_responses=True
        )
        
        self._init_storage_buckets()
    
    async def prepare_agent_memory_context(
        self,
        agent_type: str,
        task_id: str,
        task_context: str
    ) -> Dict[str, Any]:
        """Prepare memory context for fresh agent creation"""
        
        # Get relevant long-term knowledge
        long_term_context = await self.neo4j.get_relevant_context(
            agent_type, task_context
        )
        
        # Get relevant procedural knowledge
        procedural_knowledge = await self.chromadb.search_procedural_knowledge(
            agent_type, task_context
        )
        
        # Prepare initial memory state for Letta agent
        initial_memory = {
            "agent_type": agent_type,
            "task_id": task_id,
            "relevant_experience": long_term_context,
            "procedural_knowledge": procedural_knowledge,
            "creation_timestamp": datetime.now().isoformat()
        }
        
        return initial_memory
    
    async def capture_agent_learnings(
        self,
        agent_id: str,
        task_completion_data: Dict
    ) -> Dict[str, Any]:
        """Capture learnings from completed agent for long-term storage"""
        
        # Extract conversation history from Letta
        agent_memories = await self.letta_integration.get_agent_memories(agent_id)
        
        # Analyze learnings for quality and relevance
        learning_analysis = await self._analyze_agent_learnings(
            agent_memories, task_completion_data
        )
        
        # Store high-quality learnings in long-term systems
        if learning_analysis.quality_score >= 4.0:
            await self._store_validated_learnings(learning_analysis)
        
        return learning_analysis
```

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
```

## Fresh-Per-Task Agent Creation with Long-Term Memory

```python
class AgentLifecycleManager:
    """Manages fresh-per-task agent creation with long-term memory access"""
    
    async def create_agent_for_task(
        self,
        agent_type: str,
        task_id: str,
        persona_config: Dict,
        memory_access_config: Dict
    ) -> str:
        """Create fresh agent with access to long-term knowledge"""
        
        # Create new Letta agent instance
        agent_id = f"{agent_type}_{task_id}_{uuid.uuid4()}"
        
        # Inject relevant long-term memories
        relevant_memories = await self.knowledge_graph.get_relevant_context(
            agent_type=agent_type,
            task_context=task_id
        )
        
        # Create agent with pre-loaded context
        agent = await self.letta_client.create_agent(
            agent_id=agent_id,
            persona=persona_config['persona'],
            initial_context=relevant_memories,
            tools=self.get_tools_for_agent_type(agent_type)
        )
        
        return agent_id
    
    async def cleanup_agent(self, agent_id: str, preserve_learnings: bool = True):
        """Clean up agent while preserving valuable learnings"""
        
        if preserve_learnings:
            # Extract learnings before cleanup
            learnings = await self.extract_agent_learnings(agent_id)
            await self.knowledge_graph.store_learnings(learnings)
        
        # Clean up agent instance
        await self.letta_client.delete_agent(agent_id)
```

## Knowledge Graph & Semantic Search Integration

```python
class KnowledgeGraphManager:
    """Neo4j-based knowledge graph with semantic search capabilities"""
    
    def __init__(self, neo4j_driver, chromadb_client):
        self.graph_db = neo4j_driver
        self.vector_db = chromadb_client
        self.semantic_search = SemanticSearchEngine(chromadb_client)
    
    async def store_agent_learning(
        self,
        agent_type: str,
        task_context: str,
        learning: Dict[str, Any],
        confidence: float
    ):
        """Store agent learning in knowledge graph with semantic indexing"""
        
        # Create knowledge node in graph
        learning_node = await self._create_learning_node(
            agent_type, task_context, learning, confidence
        )
        
        # Create semantic embedding for search
        embedding = await self.semantic_search.create_embedding(
            learning['content']
        )
        
        # Store in vector database for semantic search
        await self.vector_db.add(
            documents=[learning['content']],
            embeddings=[embedding],
            metadatas=[{
                "agent_type": agent_type,
                "task_context": task_context,
                "graph_node_id": learning_node.id,
                "confidence": confidence
            }]
        )
        
        # Create relationships to existing knowledge
        await self._create_knowledge_relationships(learning_node, learning)
    
    async def get_relevant_context_for_agent(
        self,
        agent_type: str,
        current_task: str,
        max_results: int = 10
    ) -> List[Dict]:
        """Retrieve relevant context for fresh agent creation"""
        
        # Semantic search for relevant past learnings
        semantic_results = await self.semantic_search.search(
            query=current_task,
            filters={"agent_type": agent_type},
            n_results=max_results
        )
        
        # Graph traversal for related concepts
        graph_results = await self._graph_search_related_concepts(
            current_task, agent_type
        )
        
        # Combine and rank results
        combined_context = await self._combine_and_rank_context(
            semantic_results, graph_results, current_task
        )
        
        return combined_context
```

## Multi-Modal File Management System

```python
from typing import Dict, Optional, List
import aiofiles
from pathlib import Path
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
import pandas as pd
from docx import Document
from pptx import Presentation

class FileManagementSystem:
    """Manages creation, editing, and collaboration on office documents"""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(exist_ok=True)
        
        # Office 365 integration for collaboration
        self.sharepoint_client = self._init_sharepoint()
        
    async def create_document(
        self,
        project_id: str,
        doc_type: str,
        title: str,
        initial_content: Optional[Dict] = None
    ) -> str:
        """Create a new document for agent collaboration"""
        
        doc_id = self._generate_doc_id(project_id, doc_type)
        project_path = self.workspace_root / project_id
        project_path.mkdir(exist_ok=True)
        
        if doc_type == "word":
            doc_path = await self._create_word_doc(
                project_path, doc_id, title, initial_content
            )
        elif doc_type == "excel":
            doc_path = await self._create_excel_doc(
                project_path, doc_id, title, initial_content
            )
        elif doc_type == "powerpoint":
            doc_path = await self._create_powerpoint_doc(
                project_path, doc_id, title, initial_content
            )
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
        
        # Register in database
        await self._register_document(doc_id, project_id, doc_type, doc_path)
        
        return doc_id
    
    async def collaborate_on_document(
        self,
        doc_id: str,
        agent_ids: List[str],
        collaboration_type: str = "sequential"
    ):
        """Enable multi-agent collaboration on documents"""
        
        if collaboration_type == "sequential":
            # Agents edit one after another
            for agent_id in agent_ids:
                await self._grant_edit_access(doc_id, agent_id)
                await self._wait_for_agent_completion(doc_id, agent_id)
                await self._revoke_edit_access(doc_id, agent_id)
        
        elif collaboration_type == "parallel":
            # Agents edit different sections simultaneously
            sections = await self._divide_document_sections(doc_id, len(agent_ids))
            tasks = []
            
            for agent_id, section in zip(agent_ids, sections):
                task = self._assign_section_to_agent(doc_id, agent_id, section)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            await self._merge_parallel_edits(doc_id)
```

## Unified Search Interface

```python
class UnifiedSearchInterface:
    """Unified search across all memory types and databases"""
    
    def __init__(self, memory_manager: UnifiedMemoryManager):
        self.memory = memory_manager
    
    async def search(
        self,
        query: str,
        project_id: str,
        search_types: List[str] = ["keyword", "semantic", "relational"],
        modalities: List[str] = ["text", "document", "image", "audio", "video"],
        memory_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """Comprehensive search across all memory dimensions"""
        
        results = {}
        
        if "keyword" in search_types:
            results["keyword"] = await self._keyword_search(
                query, project_id, modalities, memory_types
            )
        
        if "semantic" in search_types:
            results["semantic"] = await self._semantic_search(
                query, project_id, modalities, memory_types
            )
        
        if "relational" in search_types:
            results["relational"] = await self._graph_search(
                query, project_id, memory_types
            )
        
        # Merge and rank results
        merged_results = await self._merge_search_results(results)
        
        return merged_results
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

databases:
  postgresql:
    url: "postgresql://user:pass@localhost:5432/atlas"
    pool_size: 20
    
  chromadb:
    host: "localhost"
    port: 8000
    persist_directory: "./chroma_data"
    
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "password"
    
  minio:
    endpoint: "localhost:9000"
    access_key: "minioadmin"
    secret_key: "minioadmin"
    secure: false
    
  redis:
    host: "localhost"
    port: 6379
    db: 0

storage:
  modalities:
    text:
      max_size: "10MB"
      formats: ["txt", "md", "json", "xml"]
      
    document:
      max_size: "100MB"
      formats: ["docx", "xlsx", "pptx", "pdf"]
      
    image:
      max_size: "50MB"
      formats: ["jpg", "png", "gif", "svg", "webp"]
      compression: true
      
    audio:
      max_size: "500MB"
      formats: ["mp3", "wav", "m4a", "flac"]
      
    video:
      max_size: "5GB"
      formats: ["mp4", "avi", "mov", "webm"]
      
    3d:
      max_size: "1GB"
      formats: ["obj", "fbx", "gltf", "stl"]

retention:
  all_permanent: true  # Override any time-based deletion
  project_association: true
  backup_strategy: "incremental"
  backup_retention: "forever"
```

This comprehensive memory architecture ensures:

1. **System knowledge** accumulates permanently to improve performance
2. **Project memories** persist appropriately with their lifecycle  
3. **Context windows** are managed intelligently based on agent roles
4. **Fresh agents** get relevant context from long-term storage
5. **Multi-modal content** is stored and searchable across all databases
6. **Knowledge relationships** are captured in the graph database
7. **Semantic search** enables intelligent context retrieval
8. **File collaboration** supports multi-agent document work