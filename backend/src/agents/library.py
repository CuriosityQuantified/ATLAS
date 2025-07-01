# /Users/nicholaspate/Documents/ATLAS/backend/src/agents/library.py

import time
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

from .base import BaseAgent, Task, TaskResult, AgentStatus
from ..agui.handlers import AGUIEventBroadcaster
from ..mlflow.tracking import ATLASMLflowTracker

class LibraryAgent(BaseAgent):
    """Library Agent - Knowledge curation and memory management service for ATLAS system."""
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        agui_broadcaster: Optional[AGUIEventBroadcaster] = None,
        mlflow_tracker: Optional[ATLASMLflowTracker] = None
    ):
        super().__init__(
            agent_id="library_agent",
            agent_type="Library Agent",
            task_id=task_id,
            agui_broadcaster=agui_broadcaster,
            mlflow_tracker=mlflow_tracker
        )
        
        # Library storage (in-memory for now, will integrate with databases later)
        self.knowledge_store: Dict[str, Any] = {
            "documents": {},        # Document storage
            "task_history": {},     # Past task records
            "patterns": {},         # Identified patterns and templates
            "project_data": {},     # Project-specific information
            "system_memory": {},    # System-wide learnings
            "agent_profiles": {},   # Agent performance and characteristics
            "search_index": {}      # Search optimization data
        }
        
        # Library statistics
        self.stats = {
            "total_entries": 0,
            "search_requests": 0,
            "successful_retrievals": 0,
            "storage_operations": 0
        }
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process library service requests from other agents."""
        await self.update_status(AgentStatus.PROCESSING, f"Processing library request: {task.task_type}")
        
        start_time = time.time()
        
        try:
            # Start MLflow run for library operation
            with self.mlflow_tracker.start_agent_run(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                task_id=task.task_id,
                parent_run_id=None
            ) as run_id:
                
                # Extract operation details from task context
                operation = task.context.get("operation", "search")
                query = task.context.get("query")
                data = task.context.get("data")
                context = task.context.get("context", {})
                
                # Route to appropriate library operation
                if operation == "search":
                    result = await self._handle_search_operation(query, context, run_id)
                elif operation == "add":
                    result = await self._handle_add_operation(data, context, run_id)
                elif operation == "modify":
                    result = await self._handle_modify_operation(query, data, context, run_id)
                elif operation == "vector_query":
                    result = await self._handle_vector_query_operation(query, context, run_id)
                elif operation == "graph_query":
                    result = await self._handle_graph_query_operation(query, context, run_id)
                elif operation == "get_stats":
                    result = await self._handle_stats_operation(context, run_id)
                else:
                    result = {"error": f"Unknown operation: {operation}", "available_operations": ["search", "add", "modify", "vector_query", "graph_query", "get_stats"]}
                
                processing_time = time.time() - start_time
                
                # Create task result
                task_result = TaskResult(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    result_type=f"library_{operation}",
                    content=result,
                    success="error" not in result,
                    processing_time=processing_time,
                    metadata={
                        "operation": operation,
                        "query_provided": query is not None,
                        "data_provided": data is not None,
                        "context_size": len(context),
                        "storage_size": len(str(self.knowledge_store))
                    },
                    requires_review=False  # Library operations don't need review
                )
                
                await self.update_status(AgentStatus.COMPLETED, f"Library {operation} completed")
                return task_result
                
        except Exception as e:
            processing_time = time.time() - start_time
            await self.update_status(AgentStatus.ERROR, f"Library operation failed: {str(e)}")
            
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="library_error",
                content={"error": "Library operation failed", "details": str(e)},
                success=False,
                processing_time=processing_time,
                errors=[str(e)]
            )
    
    async def _handle_search_operation(self, query: str, context: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Handle search operations in the knowledge store."""
        self.stats["search_requests"] += 1
        
        if not query:
            return {"error": "Search query is required"}
        
        search_type = context.get("search_type", "general")
        limit = context.get("limit", 10)
        include_patterns = context.get("include_patterns", False)
        
        results = []
        
        # Search across different knowledge categories
        if search_type in ["general", "task_history"]:
            task_matches = self._search_task_history(query, limit)
            results.extend(task_matches)
        
        if search_type in ["general", "documents"]:
            doc_matches = self._search_documents(query, limit)
            results.extend(doc_matches)
        
        if search_type in ["general", "patterns"]:
            pattern_matches = self._search_patterns(query, limit)
            results.extend(pattern_matches)
        
        # Include similar patterns if requested
        similar_patterns = []
        if include_patterns and results:
            similar_patterns = self._find_similar_patterns(query, results)
        
        # Update statistics
        if results:
            self.stats["successful_retrievals"] += 1
        
        return {
            "query": query,
            "search_type": search_type,
            "results": results[:limit],
            "total_found": len(results),
            "similar_patterns": similar_patterns,
            "search_metadata": {
                "timestamp": datetime.now().isoformat(),
                "processing_time_ms": 0,  # Placeholder for actual timing
                "categories_searched": ["task_history", "documents", "patterns"] if search_type == "general" else [search_type]
            }
        }
    
    async def _handle_add_operation(self, data: Dict[str, Any], context: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Handle adding new information to the knowledge store."""
        self.stats["storage_operations"] += 1
        
        if not data:
            return {"error": "Data is required for add operation"}
        
        category = context.get("category", "documents")
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Prepare entry with metadata
        entry = {
            "id": entry_id,
            "data": data,
            "category": category,
            "added_by": context.get("requesting_agent", "unknown"),
            "timestamp": timestamp,
            "context": context
        }
        
        # Store in appropriate category
        if category not in self.knowledge_store:
            self.knowledge_store[category] = {}
        
        self.knowledge_store[category][entry_id] = entry
        self.stats["total_entries"] += 1
        
        # Broadcast storage event
        await self.agui_broadcaster.broadcast_dialogue_update(
            task_id=self.task_id,
            agent_id=self.agent_id,
            message_id=entry_id,
            direction="output",
            content={
                "type": "knowledge_stored",
                "data": {
                    "entry_id": entry_id,
                    "category": category,
                    "data_type": data.get("type", "unknown"),
                    "size": len(str(data))
                },
                "metadata": {
                    "timestamp": timestamp,
                    "storage_location": f"{category}/{entry_id}"
                }
            },
            sender=self.agent_id
        )
        
        return {
            "status": "success",
            "entry_id": entry_id,
            "category": category,
            "stored_at": timestamp,
            "data_size": len(str(data)),
            "total_entries": self.stats["total_entries"]
        }
    
    async def _handle_modify_operation(self, query: str, data: Dict[str, Any], context: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Handle modifying existing information in the knowledge store."""
        self.stats["storage_operations"] += 1
        
        if not query or not data:
            return {"error": "Both query and data are required for modify operation"}
        
        # Search for entries to modify
        search_results = await self._handle_search_operation(query, context, run_id)
        
        if not search_results.get("results"):
            return {"error": "No entries found matching the query", "query": query}
        
        modified_entries = []
        
        # Modify matching entries
        for result in search_results["results"][:1]:  # Modify only first match for safety
            entry_id = result.get("id")
            category = result.get("category", "documents")
            
            if entry_id and entry_id in self.knowledge_store.get(category, {}):
                # Update the entry
                original_entry = self.knowledge_store[category][entry_id]
                original_entry["data"].update(data)
                original_entry["modified_at"] = datetime.now().isoformat()
                original_entry["modified_by"] = context.get("requesting_agent", "unknown")
                
                modified_entries.append({
                    "entry_id": entry_id,
                    "category": category,
                    "modifications": list(data.keys())
                })
        
        return {
            "status": "success",
            "query": query,
            "modified_entries": modified_entries,
            "total_modified": len(modified_entries)
        }
    
    async def _handle_vector_query_operation(self, query: str, context: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Handle vector similarity queries (placeholder for ChromaDB integration)."""
        # Placeholder - will integrate with ChromaDB in database phase
        return {
            "query": query,
            "vector_results": [],
            "similarity_scores": [],
            "note": "Vector query functionality will be implemented with ChromaDB integration"
        }
    
    async def _handle_graph_query_operation(self, query: str, context: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Handle graph relationship queries (placeholder for Neo4j integration)."""
        # Placeholder - will integrate with Neo4j in database phase
        return {
            "query": query,
            "graph_results": [],
            "relationships": [],
            "note": "Graph query functionality will be implemented with Neo4j integration"
        }
    
    async def _handle_stats_operation(self, context: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Handle requests for library statistics and health information."""
        return {
            "library_stats": dict(self.stats),
            "storage_summary": {
                category: len(items) for category, items in self.knowledge_store.items()
            },
            "health_status": "operational",
            "last_updated": datetime.now().isoformat(),
            "memory_usage": len(str(self.knowledge_store))
        }
    
    def _search_task_history(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search task history for relevant matches."""
        matches = []
        query_lower = query.lower()
        
        for entry_id, entry in self.knowledge_store.get("task_history", {}).items():
            data = entry.get("data", {})
            # Simple text matching (will be enhanced with vector search later)
            if (query_lower in str(data).lower() or 
                query_lower in entry.get("category", "").lower()):
                matches.append({
                    "id": entry_id,
                    "category": "task_history",
                    "data": data,
                    "relevance_score": 0.8,  # Placeholder scoring
                    "timestamp": entry.get("timestamp")
                })
        
        return sorted(matches, key=lambda x: x.get("relevance_score", 0), reverse=True)[:limit]
    
    def _search_documents(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search documents for relevant matches."""
        matches = []
        query_lower = query.lower()
        
        for entry_id, entry in self.knowledge_store.get("documents", {}).items():
            data = entry.get("data", {})
            if query_lower in str(data).lower():
                matches.append({
                    "id": entry_id,
                    "category": "documents",
                    "data": data,
                    "relevance_score": 0.7,  # Placeholder scoring
                    "timestamp": entry.get("timestamp")
                })
        
        return sorted(matches, key=lambda x: x.get("relevance_score", 0), reverse=True)[:limit]
    
    def _search_patterns(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search patterns for relevant matches."""
        matches = []
        query_lower = query.lower()
        
        for entry_id, entry in self.knowledge_store.get("patterns", {}).items():
            data = entry.get("data", {})
            if query_lower in str(data).lower():
                matches.append({
                    "id": entry_id,
                    "category": "patterns",
                    "data": data,
                    "relevance_score": 0.9,  # Patterns get higher relevance
                    "timestamp": entry.get("timestamp")
                })
        
        return sorted(matches, key=lambda x: x.get("relevance_score", 0), reverse=True)[:limit]
    
    def _find_similar_patterns(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find patterns similar to search results."""
        # Placeholder - will be enhanced with vector similarity
        return [
            {
                "pattern_type": "task_decomposition",
                "similarity_score": 0.8,
                "description": "Similar task breakdown patterns found"
            }
        ]
    
    async def get_system_prompt(self) -> str:
        """Get Library Agent specific system prompt."""
        base_prompt = await super().get_system_prompt()
        
        library_prompt = f"""{base_prompt}

LIBRARY AGENT CAPABILITIES:
- Knowledge storage and retrieval across all project categories
- Pattern recognition and similarity matching
- Cross-project information synthesis
- Search optimization and relevance ranking
- Memory management and data organization

CURRENT LIBRARY STATUS:
- Total entries: {self.stats['total_entries']}
- Search requests: {self.stats['search_requests']}
- Successful retrievals: {self.stats['successful_retrievals']}
- Storage categories: {len(self.knowledge_store)}

SUPPORTED OPERATIONS:
- search: Find relevant information using queries
- add: Store new knowledge and data
- modify: Update existing entries
- vector_query: Semantic similarity search (future)
- graph_query: Relationship queries (future)
- get_stats: Library health and statistics

As the Library Agent, focus on accurate categorization, intelligent retrieval, and helping other agents build upon previous work."""
        
        return library_prompt