# ATLAS Memory Architecture

## Overview

ATLAS implements a hybrid memory system using ChromaDB as the vector store, with both shared system-wide memory and isolated agent-specific memory. This design allows agents to learn from collective experiences while maintaining their own specialized knowledge.

## Memory Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                   System-Wide Library                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │            Shared Memory (ChromaDB)              │   │
│  │  • Global knowledge base                         │   │
│  │  • Cross-team insights                          │   │
│  │  • Task patterns & solutions                    │   │
│  │  • User preferences                             │   │
│  └─────────────────────────────────────────────────┘   │
│                           │                              │
│  ┌──────────────┬────────┴────────┬──────────────┐     │
│  │              │                 │               │     │
│  ▼              ▼                 ▼               ▼     │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│ │Research │ │Analysis │ │Writing  │ │ Rating  │      │
│ │  Team   │ │  Team   │ │  Team   │ │  Team   │      │
│ │ Memory  │ │ Memory  │ │ Memory  │ │ Memory  │      │
│ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘      │
│      │           │           │           │             │
│  ┌───┴───┐   ┌──┴──┐    ┌──┴──┐    ┌──┴──┐          │
│  │Agent 1│   │Agent│    │Agent│    │Agent│          │
│  │Memory │   │Mem. │    │Mem. │    │Mem. │          │
│  └───────┘   └─────┘    └─────┘    └─────┘          │
└─────────────────────────────────────────────────────────┘
```

## Memory Types

### 1. Shared Memory (System-Wide Library)
**Purpose**: Collective knowledge accessible by all agents
**Location**: `shared_memory` collection in ChromaDB

**Content Types**:
- **Knowledge Base**: Domain facts, definitions, concepts
- **Task Patterns**: Successful task completion strategies
- **User Context**: Preferences, historical interactions, feedback
- **Cross-Team Insights**: Learnings that benefit multiple teams
- **Quality Standards**: Rating criteria, writing guidelines

**Access Pattern**:
- Read: All agents
- Write: Through memory manager with validation
- Update: Requires consensus or supervisor approval

### 2. Team-Level Memory
**Purpose**: Team-specific knowledge and workflows
**Location**: `team_{team_name}` collections in ChromaDB

**Content Types**:
- **Team Workflows**: Proven processes and methodologies
- **Team Resources**: Preferred tools, sources, templates
- **Performance Metrics**: Success rates, efficiency data
- **Coordination Patterns**: How team members work together

### 3. Agent-Level Memory
**Purpose**: Individual agent specialization and experience
**Location**: `agent_{agent_id}` collections in ChromaDB

**Content Types**:
- **Personal Experience**: Task history, successes, failures
- **Skill Development**: Learned techniques, improvements
- **Working Memory**: Current task context, scratchpad
- **Preferences**: Individual agent optimizations

## Implementation Details

### Memory Manager Class

```python
from typing import Dict, List, Optional, Any
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
import json

class MemoryManager:
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8000):
        self.client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize all memory collections"""
        # Shared memory collection
        self.shared_memory = self.client.get_or_create_collection(
            name="shared_memory",
            embedding_function=self.embedding_fn,
            metadata={"type": "shared", "version": "1.0"}
        )
        
        # Team collections
        for team in ["research", "analysis", "writing", "rating"]:
            self.client.get_or_create_collection(
                name=f"team_{team}",
                embedding_function=self.embedding_fn,
                metadata={"type": "team", "team": team}
            )
    
    def store_memory(
        self,
        content: str,
        memory_type: str,
        agent_id: Optional[str] = None,
        team: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Store a memory in the appropriate collection"""
        collection = self._get_collection(memory_type, agent_id, team)
        
        memory_id = f"{memory_type}_{datetime.now().isoformat()}"
        metadata = metadata or {}
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "memory_type": memory_type,
            "agent_id": agent_id,
            "team": team
        })
        
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        return memory_id
    
    def retrieve_memories(
        self,
        query: str,
        memory_type: str,
        agent_id: Optional[str] = None,
        team: Optional[str] = None,
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories"""
        collection = self._get_collection(memory_type, agent_id, team)
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters
        )
        
        memories = []
        for i in range(len(results['ids'][0])):
            memories.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i]
            })
        
        return memories
    
    def _get_collection(
        self,
        memory_type: str,
        agent_id: Optional[str] = None,
        team: Optional[str] = None
    ):
        """Get the appropriate collection based on memory type"""
        if memory_type == "shared":
            return self.shared_memory
        elif memory_type == "team" and team:
            return self.client.get_collection(f"team_{team}")
        elif memory_type == "agent" and agent_id:
            return self.client.get_or_create_collection(
                name=f"agent_{agent_id}",
                embedding_function=self.embedding_fn
            )
        else:
            raise ValueError(f"Invalid memory configuration: {memory_type}")
```

### Memory Access Patterns

```python
class BaseAgent:
    def __init__(self, agent_id: str, team: str, memory_manager: MemoryManager):
        self.agent_id = agent_id
        self.team = team
        self.memory = memory_manager
    
    def remember(self, content: str, importance: str = "normal"):
        """Store a memory in agent's personal memory"""
        self.memory.store_memory(
            content=content,
            memory_type="agent",
            agent_id=self.agent_id,
            metadata={"importance": importance}
        )
    
    def recall(self, query: str, include_shared: bool = True) -> List[Dict]:
        """Recall relevant memories"""
        memories = []
        
        # Get personal memories
        personal = self.memory.retrieve_memories(
            query=query,
            memory_type="agent",
            agent_id=self.agent_id
        )
        memories.extend(personal)
        
        # Get team memories
        team_memories = self.memory.retrieve_memories(
            query=query,
            memory_type="team",
            team=self.team
        )
        memories.extend(team_memories)
        
        # Get shared memories if requested
        if include_shared:
            shared = self.memory.retrieve_memories(
                query=query,
                memory_type="shared"
            )
            memories.extend(shared)
        
        # Sort by relevance (distance)
        memories.sort(key=lambda x: x['distance'])
        return memories[:10]  # Return top 10 most relevant
    
    def contribute_to_shared(self, content: str, requires_approval: bool = True):
        """Contribute knowledge to shared memory"""
        if requires_approval:
            # Queue for supervisor approval
            self._queue_for_approval(content)
        else:
            self.memory.store_memory(
                content=content,
                memory_type="shared",
                metadata={"contributor": self.agent_id, "team": self.team}
            )
```

## Memory Lifecycle

### 1. Memory Creation
- Agents generate memories during task execution
- Memories are tagged with context, timestamp, and importance
- Automatic embedding generation for semantic search

### 2. Memory Consolidation
- Periodic review of agent memories for promotion to team/shared
- Duplicate detection and merging
- Quality scoring based on usage and feedback

### 3. Memory Retrieval
- Semantic search using embeddings
- Metadata filtering (time, agent, importance)
- Ranked results by relevance

### 4. Memory Evolution
- Update existing memories with new information
- Track memory usage patterns
- Decay unused memories over time

## Configuration

### Environment Variables
```bash
# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./chroma_data

# Memory Settings
MEMORY_EMBEDDING_MODEL=text-embedding-3-small
MEMORY_MAX_RESULTS=10
MEMORY_CONSOLIDATION_INTERVAL=3600  # seconds

# Access Control
SHARED_MEMORY_WRITE_APPROVAL=true
MEMORY_RETENTION_DAYS=90
```

### Memory Quotas
```python
MEMORY_LIMITS = {
    "shared": {
        "max_entries": 100000,
        "max_size_mb": 5000
    },
    "team": {
        "max_entries": 50000,
        "max_size_mb": 2000
    },
    "agent": {
        "max_entries": 10000,
        "max_size_mb": 500
    }
}
```

## Best Practices

1. **Memory Hygiene**
   - Regular cleanup of outdated memories
   - Consolidation of similar memories
   - Version control for important shared memories

2. **Access Patterns**
   - Cache frequently accessed shared memories
   - Batch memory operations when possible
   - Use metadata filters before semantic search

3. **Privacy & Security**
   - No sensitive data in shared memory
   - Audit trail for shared memory modifications
   - Role-based access for memory management

4. **Performance**
   - Index optimization for common queries
   - Asynchronous memory operations
   - Connection pooling for ChromaDB