# ATLAS Database Architecture: Multi-Provider Data Flow Strategy

## Overview

ATLAS uses a multi-database architecture where each database type serves specific purposes optimized for different data patterns and access requirements. Data flows seamlessly between systems while maintaining consistency and performance.

## Database Provider Responsibilities

### PostgreSQL - Primary Operational Database
```python
# Core operational data storage
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

class PostgreSQLManager:
    """Primary operational database management"""
    
    def __init__(self, config: Dict):
        self.engine = create_async_engine(config['connection_string'])
        self.session_factory = async_sessionmaker(self.engine)
    
    async def store_task_metadata(self, task: Dict) -> str:
        """Store task definition and metadata"""
        async with self.session_factory() as session:
            task_record = TaskMetadata(
                task_id=task['id'],
                user_id=task['user_id'],
                task_type=task['type'],
                complexity=task['complexity'],
                status='pending',
                created_at=datetime.now(),
                configuration=task['config'],
                parent_task_id=task.get('parent_task_id')
            )
            session.add(task_record)
            await session.commit()
            return task_record.task_id
    
    async def get_agent_configuration(self, agent_type: str) -> Dict:
        """Retrieve agent configuration by type"""
        async with self.session_factory() as session:
            config = await session.execute(
                select(AgentConfiguration).where(
                    AgentConfiguration.agent_type == agent_type
                )
            )
            return config.scalar_one().to_dict()
    
    async def track_agent_performance(
        self, 
        agent_id: str, 
        metrics: Dict
    ):
        """Track agent performance metrics"""
        async with self.session_factory() as session:
            performance_record = AgentPerformance(
                agent_id=agent_id,
                task_id=metrics['task_id'],
                execution_time=metrics['execution_time'],
                quality_score=metrics['quality_score'],
                error_count=metrics['error_count'],
                tokens_used=metrics['tokens_used'],
                cost=metrics['cost'],
                timestamp=datetime.now()
            )
            session.add(performance_record)
            await session.commit()
```

### ChromaDB - Vector Embeddings & Semantic Search
```python
# Semantic search and similarity matching
CHROMADB_RESPONSIBILITIES = {
    'document_embeddings': 'Semantic search across processed documents',
    'memory_embeddings': 'Agent memory search and context retrieval',
    'task_similarity': 'Find similar past tasks for context',
    'knowledge_search': 'Semantic search across knowledge base',
    'agent_expertise': 'Match agents to tasks based on past performance',
    'content_similarity': 'Duplicate detection and content clustering'
}

class ChromaDBManager:
    """Vector database for semantic search"""
    
    def __init__(self, config: Dict):
        self.client = chromadb.AsyncHttpClient(
            host=config['host'],
            port=config['port']
        )
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        self.collections = {}
    
    async def initialize_collections(self):
        """Initialize required collections for ATLAS"""
        collections_config = {
            'agent_memories': {
                'metadata_fields': ['agent_type', 'task_type', 'confidence', 'timestamp'],
                'distance_metric': 'cosine'
            },
            'document_content': {
                'metadata_fields': ['document_type', 'source', 'quality_score'],
                'distance_metric': 'cosine'  
            },
            'task_contexts': {
                'metadata_fields': ['complexity', 'domain', 'outcome'],
                'distance_metric': 'cosine'
            },
            'procedural_knowledge': {
                'metadata_fields': ['skill_type', 'success_rate', 'agent_type'],
                'distance_metric': 'cosine'
            }
        }
        
        for collection_name, config in collections_config.items():
            collection = await self.client.get_or_create_collection(
                name=f"atlas_{collection_name}",
                embedding_function=self.embedding_function,
                metadata=config
            )
            self.collections[collection_name] = collection
    
    async def store_agent_memory(
        self,
        agent_type: str,
        content: str,
        task_context: Dict,
        confidence: float
    ):
        """Store agent memory with semantic indexing"""
        
        memory_id = f"memory_{uuid.uuid4()}"
        
        await self.collections['agent_memories'].add(
            documents=[content],
            metadatas=[{
                'agent_type': agent_type,
                'task_type': task_context.get('type'),
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'task_id': task_context.get('task_id')
            }],
            ids=[memory_id]
        )
        
        return memory_id
    
    async def search_relevant_memories(
        self,
        query: str,
        agent_type: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search for relevant memories using semantic similarity"""
        
        where_filter = {}
        if agent_type:
            where_filter['agent_type'] = agent_type
        
        results = await self.collections['agent_memories'].query(
            query_texts=[query],
            n_results=limit,
            where=where_filter if where_filter else None
        )
        
        return [
            {
                'content': doc,
                'metadata': meta,
                'similarity': 1 - distance  # Convert distance to similarity
            }
            for doc, meta, distance in zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )
        ]
```

### Neo4j - Knowledge Graph & Relationships
```python
# Relationship modeling and graph analysis
NEO4J_RESPONSIBILITIES = {
    'concept_relationships': 'Model relationships between concepts and entities',
    'agent_collaboration': 'Track successful agent combinations and patterns',
    'knowledge_provenance': 'Track source and derivation of knowledge',
    'task_dependencies': 'Model complex task interdependencies',
    'learning_paths': 'Track how knowledge builds over time',
    'domain_expertise': 'Map expertise areas and knowledge domains'
}

class Neo4jManager:
    """Knowledge graph and relationship management"""
    
    def __init__(self, config: Dict):
        self.driver = neo4j.AsyncGraphDatabase.driver(
            config['uri'],
            auth=(config['user'], config['password'])
        )
    
    async def create_knowledge_node(
        self,
        knowledge_type: str,
        content: Dict,
        source_info: Dict
    ) -> str:
        """Create knowledge node with metadata"""
        
        async with self.driver.session() as session:
            result = await session.run(
                """
                CREATE (k:Knowledge {
                    id: $id,
                    type: $type,
                    content: $content,
                    confidence: $confidence,
                    created_at: datetime(),
                    source: $source,
                    validated: $validated
                })
                RETURN k.id as node_id
                """,
                id=str(uuid.uuid4()),
                type=knowledge_type,
                content=json.dumps(content),
                confidence=content.get('confidence', 0.5),
                source=json.dumps(source_info),
                validated=content.get('validated', False)
            )
            
            record = await result.single()
            return record['node_id']
    
    async def create_agent_collaboration_relationship(
        self,
        agent_1_id: str,
        agent_2_id: str,
        collaboration_outcome: Dict
    ):
        """Track successful agent collaborations"""
        
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (a1:Agent {id: $agent1_id})
                MERGE (a2:Agent {id: $agent2_id})
                CREATE (a1)-[c:COLLABORATED_WITH {
                    task_type: $task_type,
                    success_score: $success_score,
                    timestamp: datetime(),
                    outcome: $outcome
                }]->(a2)
                """,
                agent1_id=agent_1_id,
                agent2_id=agent_2_id,
                task_type=collaboration_outcome.get('task_type'),
                success_score=collaboration_outcome.get('success_score'),
                outcome=json.dumps(collaboration_outcome)
            )
    
    async def find_related_concepts(
        self,
        concept: str,
        relationship_types: List[str] = None,
        max_depth: int = 3
    ) -> List[Dict]:
        """Find concepts related to input concept"""
        
        relationship_filter = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            relationship_filter = f":{types_str}"
        
        async with self.driver.session() as session:
            result = await session.run(
                f"""
                MATCH (start:Concept {{name: $concept}})
                MATCH (start)-[r{relationship_filter}*1..{max_depth}]-(related:Concept)
                RETURN DISTINCT related.name as concept,
                       type(r) as relationship_type,
                       length(path) as distance
                ORDER BY distance, related.name
                LIMIT 20
                """,
                concept=concept
            )
            
            return [
                {
                    'concept': record['concept'],
                    'relationship_type': record['relationship_type'],
                    'distance': record['distance']
                }
                async for record in result
            ]
    
    async def get_agent_expertise_graph(self, agent_type: str) -> Dict:
        """Get expertise graph for agent type"""
        
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (a:Agent {type: $agent_type})-[e:EXPERT_IN]->(d:Domain)
                MATCH (d)-[r:RELATED_TO]-(rd:Domain)
                RETURN d.name as primary_domain,
                       e.proficiency as proficiency,
                       collect(rd.name) as related_domains
                """,
                agent_type=agent_type
            )
            
            expertise_map = {}
            async for record in result:
                expertise_map[record['primary_domain']] = {
                    'proficiency': record['proficiency'],
                    'related_domains': record['related_domains']
                }
            
            return expertise_map
```

### Redis - Caching & Session Management
```python
# High-speed caching and temporary data
REDIS_RESPONSIBILITIES = {
    'session_cache': 'Active user sessions and temporary state',
    'api_response_cache': 'Cache expensive API responses',
    'rate_limiting': 'Track API usage and enforce limits',
    'real_time_coordination': 'Agent coordination and messaging',
    'temporary_results': 'Intermediate task results and working data',
    'model_performance_cache': 'Cache model performance metrics'
}

class RedisManager:
    """High-speed caching and session management"""
    
    def __init__(self, config: Dict):
        self.redis = aioredis.from_url(
            f"redis://{config['host']}:{config['port']}/{config['db']}"
        )
        self.default_ttl = config.get('default_ttl', 3600)  # 1 hour
    
    async def cache_agent_context(
        self,
        agent_id: str,
        context: Dict,
        ttl: int = None
    ):
        """Cache agent context for quick access"""
        
        cache_key = f"agent_context:{agent_id}"
        ttl = ttl or self.default_ttl
        
        await self.redis.setex(
            cache_key,
            ttl,
            json.dumps(context, default=str)
        )
    
    async def get_agent_context(self, agent_id: str) -> Dict:
        """Retrieve cached agent context"""
        
        cache_key = f"agent_context:{agent_id}"
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def track_api_usage(
        self,
        provider: str,
        model: str,
        tokens_used: int
    ):
        """Track API usage for rate limiting"""
        
        current_hour = datetime.now().strftime("%Y%m%d%H")
        usage_key = f"api_usage:{provider}:{model}:{current_hour}"
        
        # Increment usage counter
        await self.redis.hincrby(usage_key, "tokens", tokens_used)
        await self.redis.hincrby(usage_key, "requests", 1)
        
        # Set expiration to 2 hours
        await self.redis.expire(usage_key, 7200)
    
    async def check_rate_limit(
        self,
        provider: str,
        model: str,
        limit: int
    ) -> bool:
        """Check if rate limit is exceeded"""
        
        current_hour = datetime.now().strftime("%Y%m%d%H")
        usage_key = f"api_usage:{provider}:{model}:{current_hour}"
        
        current_usage = await self.redis.hget(usage_key, "tokens")
        current_usage = int(current_usage) if current_usage else 0
        
        return current_usage < limit
```

### MinIO/S3 - File Storage & Multi-Modal Content
```python
# File storage and multi-modal content management
MINIO_RESPONSIBILITIES = {
    'document_storage': 'Store original documents and processed versions',
    'media_files': 'Audio, video, images from multi-modal interactions',
    'model_artifacts': 'Store fine-tuned models and embeddings',
    'backup_data': 'Database backups and checkpoint files',
    'export_files': 'Generated reports, presentations, exports',
    'temporary_files': 'Large temporary files during processing'
}

class MinIOManager:
    """Object storage for files and multi-modal content"""
    
    def __init__(self, config: Dict):
        self.client = Minio(
            config['endpoint'],
            access_key=config['access_key'],
            secret_key=config['secret_key'],
            secure=config.get('secure', True)
        )
        self.bucket_name = config['bucket_name']
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure bucket exists for ATLAS storage"""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
    
    async def store_document(
        self,
        document_content: bytes,
        document_type: str,
        metadata: Dict
    ) -> str:
        """Store document with metadata"""
        
        object_name = f"documents/{document_type}/{uuid.uuid4()}"
        
        # Add metadata
        metadata_headers = {
            f"x-amz-meta-{key}": str(value)
            for key, value in metadata.items()
        }
        
        self.client.put_object(
            self.bucket_name,
            object_name,
            io.BytesIO(document_content),
            length=len(document_content),
            content_type=self._get_content_type(document_type),
            metadata=metadata_headers
        )
        
        return object_name
    
    async def get_document(self, object_name: str) -> bytes:
        """Retrieve document content"""
        
        response = self.client.get_object(self.bucket_name, object_name)
        content = response.read()
        response.close()
        response.release_conn()
        
        return content
    
    async def store_checkpoint(
        self,
        task_id: str,
        checkpoint_data: Dict
    ) -> str:
        """Store task checkpoint data"""
        
        checkpoint_name = f"checkpoints/{task_id}/{datetime.now().isoformat()}.json"
        checkpoint_content = json.dumps(checkpoint_data, default=str).encode()
        
        self.client.put_object(
            self.bucket_name,
            checkpoint_name,
            io.BytesIO(checkpoint_content),
            length=len(checkpoint_content),
            content_type="application/json"
        )
        
        return checkpoint_name
```

## Data Flow Patterns

### Agent Creation Data Flow
```python
class AgentCreationDataFlow:
    """Coordinate data flow during agent creation"""
    
    async def create_agent_with_context(
        self,
        agent_type: str,
        task_id: str,
        user_id: str
    ) -> str:
        """Create agent with full context from all data sources"""
        
        # 1. Get agent configuration from PostgreSQL
        agent_config = await self.postgres.get_agent_configuration(agent_type)
        
        # 2. Get relevant memories from ChromaDB
        task_context = await self.postgres.get_task_metadata(task_id)
        relevant_memories = await self.chromadb.search_relevant_memories(
            query=task_context['description'],
            agent_type=agent_type,
            limit=5
        )
        
        # 3. Get related knowledge from Neo4j
        related_concepts = await self.neo4j.find_related_concepts(
            concept=task_context['domain'],
            max_depth=2
        )
        
        # 4. Check for cached context in Redis
        cached_context = await self.redis.get_agent_context(f"{agent_type}:{task_id}")
        
        # 5. Combine all context
        full_context = {
            'agent_config': agent_config,
            'relevant_memories': relevant_memories,
            'related_knowledge': related_concepts,
            'cached_context': cached_context,
            'task_metadata': task_context
        }
        
        # 6. Create agent in Letta with context
        agent_id = await self.letta_client.create_agent(
            agent_type=agent_type,
            initial_context=full_context,
            tools=agent_config['tools']
        )
        
        # 7. Cache agent context in Redis
        await self.redis.cache_agent_context(agent_id, full_context)
        
        # 8. Track agent creation in PostgreSQL
        await self.postgres.track_agent_creation(agent_id, task_id, user_id)
        
        return agent_id

class TaskCompletionDataFlow:
    """Coordinate data flow when task completes"""
    
    async def process_task_completion(
        self,
        task_id: str,
        agent_id: str,
        results: Dict
    ):
        """Process and store all data from completed task"""
        
        # 1. Extract learnings from Letta agent
        agent_memories = await self.letta_client.get_agent_memories(agent_id)
        
        # 2. Analyze and quality-check learnings
        learning_analysis = await self.librarian.analyze_learnings(
            agent_memories, results
        )
        
        # 3. Store high-quality learnings
        if learning_analysis.quality_score >= 4.0:
            # Store in ChromaDB for semantic search
            memory_id = await self.chromadb.store_agent_memory(
                agent_type=results['agent_type'],
                content=learning_analysis.summary,
                task_context=results,
                confidence=learning_analysis.confidence
            )
            
            # Store in Neo4j for relationship mapping
            knowledge_node = await self.neo4j.create_knowledge_node(
                knowledge_type='agent_learning',
                content=learning_analysis.summary,
                source_info={'agent_id': agent_id, 'task_id': task_id}
            )
            
            # Link to related concepts
            await self.neo4j.create_knowledge_relationships(
                knowledge_node, learning_analysis.related_concepts
            )
        
        # 4. Update performance metrics in PostgreSQL
        await self.postgres.track_agent_performance(
            agent_id=agent_id,
            metrics={
                'task_id': task_id,
                'execution_time': results['execution_time'],
                'quality_score': learning_analysis.quality_score,
                'error_count': results.get('error_count', 0),
                'tokens_used': results.get('tokens_used', 0),
                'cost': results.get('cost', 0)
            }
        )
        
        # 5. Store any files in MinIO
        if results.get('generated_files'):
            for file_data in results['generated_files']:
                file_path = await self.minio.store_document(
                    document_content=file_data['content'],
                    document_type=file_data['type'],
                    metadata={
                        'task_id': task_id,
                        'agent_id': agent_id,
                        'created_at': datetime.now().isoformat()
                    }
                )
                
                # Link file to task in PostgreSQL
                await self.postgres.link_file_to_task(task_id, file_path)
        
        # 6. Clear temporary cache data
        await self.redis.delete(f"agent_context:{agent_id}")
        
        # 7. Clean up Letta agent
        await self.letta_client.delete_agent(agent_id)
```

## Data Consistency & Synchronization

```python
class DataConsistencyManager:
    """Ensure data consistency across multiple databases"""
    
    async def sync_knowledge_across_systems(
        self,
        knowledge_item: Dict
    ):
        """Synchronize knowledge across vector and graph databases"""
        
        try:
            # Start transaction-like operation
            sync_id = str(uuid.uuid4())
            
            # 1. Store in ChromaDB for semantic search
            vector_id = await self.chromadb.store_knowledge(
                content=knowledge_item['content'],
                metadata={
                    'sync_id': sync_id,
                    'type': knowledge_item['type'],
                    'confidence': knowledge_item['confidence']
                }
            )
            
            # 2. Store in Neo4j for relationship modeling
            graph_node_id = await self.neo4j.create_knowledge_node(
                knowledge_type=knowledge_item['type'],
                content=knowledge_item,
                source_info={'sync_id': sync_id, 'vector_id': vector_id}
            )
            
            # 3. Update PostgreSQL with references
            await self.postgres.store_knowledge_references(
                sync_id=sync_id,
                vector_id=vector_id,
                graph_node_id=graph_node_id,
                metadata=knowledge_item
            )
            
            # 4. Cache for quick access
            await self.redis.cache_knowledge_references(
                sync_id, {'vector_id': vector_id, 'graph_node_id': graph_node_id}
            )
            
            return sync_id
            
        except Exception as e:
            # Rollback operations
            await self._rollback_knowledge_sync(sync_id)
            raise KnowledgeSyncError(f"Failed to sync knowledge: {e}")
    
    async def _rollback_knowledge_sync(self, sync_id: str):
        """Rollback failed sync operation"""
        
        # Best effort cleanup
        try:
            await self.chromadb.delete_by_metadata({'sync_id': sync_id})
        except:
            pass
            
        try:
            await self.neo4j.delete_nodes_by_source({'sync_id': sync_id})
        except:
            pass
            
        try:
            await self.postgres.delete_knowledge_references(sync_id)
        except:
            pass
            
        try:
            await self.redis.delete(f"knowledge_refs:{sync_id}")
        except:
            pass
```

This multi-database architecture provides:

1. **Optimal Data Placement**: Each database serves its strengths
2. **Seamless Data Flow**: Coordinated data movement between systems
3. **Consistency Management**: Transaction-like operations across databases
4. **Performance Optimization**: Caching and efficient access patterns
5. **Scalability**: Each database can scale independently
6. **Fault Tolerance**: Graceful degradation when components fail

The system ensures ATLAS can handle complex multi-modal data while maintaining performance and reliability at scale.