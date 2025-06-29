# ATLAS Multi-Modal Memory & File Management Architecture

## Overview

ATLAS implements a comprehensive memory system supporting multiple database types (structured, unstructured, vector, graph) and various data modalities (text, images, audio, video, 3D). All memory types persist permanently with project-based organization to maintain complete historical context.

## Database Architecture

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

## Multi-Database Memory Manager

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
    
    async def store_memory(
        self,
        content: Any,
        memory_type: str,
        modality: str,
        project_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Store memory across appropriate databases"""
        
        memory_id = self._generate_memory_id(project_id, memory_type)
        
        # Store metadata in PostgreSQL
        await self._store_metadata(memory_id, memory_type, modality, project_id, metadata)
        
        # Store content based on modality
        if modality == "text":
            await self._store_text_memory(memory_id, content, metadata)
        elif modality in ["image", "video", "audio", "3d"]:
            await self._store_media_memory(memory_id, content, modality, metadata)
        elif modality == "document":
            await self._store_document_memory(memory_id, content, metadata)
        
        # Update knowledge graph
        await self._update_knowledge_graph(memory_id, content, metadata)
        
        return memory_id
    
    async def _store_text_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """Store text in vector DB with embeddings"""
        
        # Generate embedding
        embedding = await self._generate_embedding(content)
        
        # Store in ChromaDB
        collection = self.chroma_client.get_or_create_collection(
            name=f"project_{metadata['project_id']}"
        )
        
        collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        # Also store in PostgreSQL for keyword search
        await self._store_text_structured(memory_id, content, metadata)
    
    async def _store_media_memory(
        self,
        memory_id: str,
        content: bytes,
        modality: str,
        metadata: Dict[str, Any]
    ):
        """Store media files in object storage"""
        
        bucket_name = f"{modality}-{metadata['project_id']}"
        
        # Ensure bucket exists
        if not self.minio_client.bucket_exists(bucket_name):
            self.minio_client.make_bucket(bucket_name)
        
        # Store file
        file_name = f"{memory_id}.{self._get_file_extension(modality)}"
        self.minio_client.put_object(
            bucket_name,
            file_name,
            content,
            length=len(content)
        )
        
        # Extract and store features for search
        features = await self._extract_media_features(content, modality)
        await self._store_media_features(memory_id, features, metadata)
    
    async def _update_knowledge_graph(
        self,
        memory_id: str,
        content: Any,
        metadata: Dict[str, Any]
    ):
        """Update Neo4j knowledge graph with relationships"""
        
        with self.neo4j_driver.session() as session:
            # Create memory node
            session.run("""
                MERGE (m:Memory {id: $memory_id})
                SET m += $properties
                """,
                memory_id=memory_id,
                properties={
                    "type": metadata['memory_type'],
                    "modality": metadata['modality'],
                    "created_at": metadata['created_at'],
                    "project_id": metadata['project_id']
                }
            )
            
            # Link to project
            session.run("""
                MATCH (m:Memory {id: $memory_id})
                MERGE (p:Project {id: $project_id})
                MERGE (m)-[:BELONGS_TO]->(p)
                """,
                memory_id=memory_id,
                project_id=metadata['project_id']
            )
            
            # Extract and link entities
            entities = await self._extract_entities(content)
            for entity in entities:
                session.run("""
                    MATCH (m:Memory {id: $memory_id})
                    MERGE (e:Entity {name: $entity_name, type: $entity_type})
                    MERGE (m)-[:MENTIONS]->(e)
                    """,
                    memory_id=memory_id,
                    entity_name=entity['name'],
                    entity_type=entity['type']
                )
```

## File Management System

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
    
    async def _create_word_doc(
        self,
        project_path: Path,
        doc_id: str,
        title: str,
        content: Optional[Dict] = None
    ) -> Path:
        """Create a Word document"""
        
        doc = Document()
        doc.add_heading(title, 0)
        
        if content:
            for section in content.get('sections', []):
                doc.add_heading(section['title'], level=1)
                doc.add_paragraph(section['content'])
        
        doc_path = project_path / f"{doc_id}.docx"
        doc.save(str(doc_path))
        
        return doc_path
    
    async def _create_excel_doc(
        self,
        project_path: Path,
        doc_id: str,
        title: str,
        content: Optional[Dict] = None
    ) -> Path:
        """Create an Excel document"""
        
        doc_path = project_path / f"{doc_id}.xlsx"
        
        with pd.ExcelWriter(str(doc_path), engine='xlsxwriter') as writer:
            if content and 'sheets' in content:
                for sheet in content['sheets']:
                    df = pd.DataFrame(sheet['data'])
                    df.to_excel(writer, sheet_name=sheet['name'], index=False)
            else:
                # Create empty sheet
                pd.DataFrame().to_excel(writer, sheet_name='Sheet1')
        
        return doc_path
    
    async def _create_powerpoint_doc(
        self,
        project_path: Path,
        doc_id: str,
        title: str,
        content: Optional[Dict] = None
    ) -> Path:
        """Create a PowerPoint presentation"""
        
        prs = Presentation()
        
        # Title slide
        title_slide = prs.slides.add_slide(prs.slide_layouts[0])
        title_slide.shapes.title.text = title
        
        if content and 'slides' in content:
            for slide_content in content['slides']:
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                slide.shapes.title.text = slide_content['title']
                slide.shapes.placeholders[1].text = slide_content['content']
        
        doc_path = project_path / f"{doc_id}.pptx"
        prs.save(str(doc_path))
        
        return doc_path
    
    async def edit_document(
        self,
        doc_id: str,
        changes: Dict[str, Any],
        agent_id: str
    ) -> bool:
        """Edit an existing document with version control"""
        
        doc_info = await self._get_document_info(doc_id)
        doc_path = Path(doc_info['path'])
        
        # Create backup before editing
        await self._create_backup(doc_path, agent_id)
        
        if doc_info['type'] == 'word':
            await self._edit_word_doc(doc_path, changes)
        elif doc_info['type'] == 'excel':
            await self._edit_excel_doc(doc_path, changes)
        elif doc_info['type'] == 'powerpoint':
            await self._edit_powerpoint_doc(doc_path, changes)
        
        # Log the edit
        await self._log_edit(doc_id, agent_id, changes)
        
        return True
    
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

## Memory Search Interface

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
    
    async def _keyword_search(
        self,
        query: str,
        project_id: str,
        modalities: List[str],
        memory_types: Optional[List[str]]
    ) -> List[Dict]:
        """PostgreSQL full-text search"""
        
        sql = """
        SELECT m.*, ts_rank(m.search_vector, query) as rank
        FROM memories m, plainto_tsquery('english', %s) query
        WHERE m.project_id = %s
        AND m.search_vector @@ query
        """
        
        params = [query, project_id]
        
        if modalities:
            sql += " AND m.modality = ANY(%s)"
            params.append(modalities)
        
        if memory_types:
            sql += " AND m.memory_type = ANY(%s)"
            params.append(memory_types)
        
        sql += " ORDER BY rank DESC LIMIT 20"
        
        # Execute query
        results = await self.memory.execute_sql(sql, params)
        return results
    
    async def _semantic_search(
        self,
        query: str,
        project_id: str,
        modalities: List[str],
        memory_types: Optional[List[str]]
    ) -> List[Dict]:
        """ChromaDB vector similarity search"""
        
        collection = self.memory.chroma_client.get_collection(
            name=f"project_{project_id}"
        )
        
        # Build where clause
        where = {"project_id": project_id}
        if modalities:
            where["modality"] = {"$in": modalities}
        if memory_types:
            where["memory_type"] = {"$in": memory_types}
        
        results = collection.query(
            query_texts=[query],
            n_results=20,
            where=where
        )
        
        return self._format_chroma_results(results)
    
    async def _graph_search(
        self,
        query: str,
        project_id: str,
        memory_types: Optional[List[str]]
    ) -> List[Dict]:
        """Neo4j graph traversal search"""
        
        with self.memory.neo4j_driver.session() as session:
            # Find entities mentioned in query
            entities = await self._extract_query_entities(query)
            
            cypher = """
            MATCH (m:Memory)-[:MENTIONS]->(e:Entity)
            WHERE m.project_id = $project_id
            AND e.name IN $entities
            """
            
            if memory_types:
                cypher += " AND m.type IN $memory_types"
            
            cypher += """
            WITH m, COUNT(DISTINCT e) as entity_count
            ORDER BY entity_count DESC
            LIMIT 20
            RETURN m
            """
            
            result = session.run(
                cypher,
                project_id=project_id,
                entities=[e['name'] for e in entities],
                memory_types=memory_types
            )
            
            return [record["m"] for record in result]
```

## Storage Configuration

```yaml
# storage-config.yaml
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

## Project-Based Memory Organization

```python
class ProjectMemoryManager:
    """Manages all memory types associated with projects"""
    
    def __init__(self, unified_memory: UnifiedMemoryManager):
        self.memory = unified_memory
    
    async def create_project_workspace(
        self,
        project_id: str,
        project_metadata: Dict[str, Any]
    ):
        """Initialize complete memory workspace for a project"""
        
        # Create project in all databases
        await self._create_postgresql_schema(project_id)
        await self._create_chromadb_collections(project_id)
        await self._create_neo4j_project_node(project_id, project_metadata)
        await self._create_minio_buckets(project_id)
        
        # Initialize file workspace
        await self._create_file_directories(project_id)
        
    async def restore_project_context(
        self,
        project_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restore complete project context including all memory types"""
        
        context = {
            "project_id": project_id,
            "working_memory": await self._restore_working_memory(project_id, session_id),
            "short_term_memory": await self._restore_short_term_memory(project_id),
            "episodic_memory": await self._restore_episodic_memory(project_id),
            "long_term_insights": await self._get_project_insights(project_id),
            "files": await self._list_project_files(project_id),
            "knowledge_graph": await self._get_project_graph_summary(project_id)
        }
        
        return context
    
    async def archive_project(
        self,
        project_id: str,
        archive_location: str
    ):
        """Archive project while maintaining accessibility"""
        
        # Create comprehensive backup
        backup_id = await self._create_full_backup(project_id)
        
        # Move to cold storage but keep indexes
        await self._move_to_cold_storage(project_id, archive_location)
        
        # Maintain quick access index
        await self._update_archive_index(project_id, backup_id, archive_location)
```

This comprehensive architecture ensures:

1. **Multi-database support** for keyword, semantic, and graph-based search
2. **All memory types persist permanently** with project association
3. **Multi-modal storage** for text, documents, images, audio, video, and 3D
4. **File management** with Office document creation and collaboration
5. **Project-based organization** allowing complete context restoration
6. **Unified search** across all databases and modalities