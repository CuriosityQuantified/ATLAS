# SNAPSHOT: Changes made to backend/src/agents/base.py for MLflow integration

# Key changes made:
# 1. Added mlflow_tracker parameter to BaseAgent.__init__()
# 2. Updated update_status() to log to both enhanced and legacy trackers  
# 3. Enhanced call_library() to log comprehensive tool call metadata
# 4. Updated delegate_task() to log agent communications with full context
# 5. System prompts (YAML personas) automatically logged on agent initialization

# Modified __init__ method:
def __init__(
    self,
    agent_id: str,
    agent_type: str,
    task_id: Optional[str] = None,
    agui_broadcaster: Optional[AGUIEventBroadcaster] = None,
    mlflow_tracker = None  # Enhanced MLflow tracker for comprehensive monitoring
):
    """Initialize base agent with comprehensive tracking."""
    self.agent_id = agent_id
    self.agent_type = agent_type
    self.task_id = task_id
    self.agui_broadcaster = agui_broadcaster or AGUIEventBroadcaster(connection_manager=None)
    self.mlflow_tracker = mlflow_tracker  # Store the enhanced MLflow tracker
    
    # Rest of initialization...
    self.call_model = CallModel(
        task_id=task_id,
        agent_id=agent_id,
        agui_broadcaster=self.agui_broadcaster,
        mlflow_tracker=mlflow_tracker
    )

# Enhanced update_status method:
async def update_status(self, new_status: AgentStatus, reason: str = ""):
    """Update agent status with comprehensive logging."""
    old_status = self.status
    self.status = new_status
    self.status_history.append((new_status, reason, datetime.now()))
    
    # Track status change with both enhanced and legacy trackers
    if self.mlflow_tracker:
        try:
            # Enhanced tracking with detailed context
            self.mlflow_tracker.log_agent_status_change(
                agent_id=self.agent_id,
                old_status=old_status.value if hasattr(old_status, 'value') else str(old_status),
                new_status=new_status.value,
                reason=reason,
                context={
                    "agent_type": self.agent_type,
                    "task_id": self.task_id,
                    "timestamp": datetime.now().isoformat(),
                    "status_history_length": len(self.status_history)
                }
            )
            
            # Legacy tracking for backward compatibility  
            if hasattr(self.mlflow_tracker, 'log_agent_status_change'):
                self.mlflow_tracker.log_agent_status_change(
                    agent_id=self.agent_id,
                    old_status=old_status.value if hasattr(old_status, 'value') else str(old_status),
                    new_status=new_status.value,
                    reason=reason
                )
        except Exception as e:
            logger.warning(f"Failed to log status change to MLflow: {e}")

# Enhanced call_library method:
async def call_library(self, operation: str, query: Optional[str] = None, 
                      data: Optional[Dict[str, Any]] = None,
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call library operations with comprehensive tracking."""
    if not self.library_agent:
        from .library import LibraryAgent
        self.library_agent = LibraryAgent(
            task_id=self.task_id,
            agui_broadcaster=self.agui_broadcaster,
            mlflow_tracker=self.mlflow_tracker
        )
    
    start_time = time.time()
    
    try:
        # Create library task
        library_task = Task(
            task_id=f"{self.task_id}_lib_{int(time.time())}",
            task_type="library_operation",
            description=f"Library {operation} operation",
            context={
                "operation": operation,
                "query": query,
                "data": data,
                "context": context or {},
                "requesting_agent": self.agent_id
            }
        )
        
        # Process library request
        result = await self.library_agent.process_task(library_task)
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Enhanced tracking with detailed metadata
        if self.mlflow_tracker:
            try:
                # Log as tool call with comprehensive metadata
                self.mlflow_tracker.log_tool_call(
                    agent_id=self.agent_id,
                    tool_name="library",
                    tool_type="library",
                    input_parameters={
                        "operation": operation,
                        "query": query,
                        "data": data,
                        "context": context or {}
                    },
                    output_result=result.content if result else None,
                    processing_time_ms=processing_time,
                    success=result.success if result else False,
                    error_message=result.errors[0] if result and result.errors else None,
                    tool_metadata={
                        "library_agent_id": self.library_agent.agent_id,
                        "task_id": library_task.task_id,
                        "operation_type": operation,
                        "has_query": query is not None,
                        "has_data": data is not None,
                        "context_keys": list(context.keys()) if context else []
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log library call to MLflow: {e}")
        
        return {
            "success": result.success if result else False,
            "result": result.content if result else None,
            "processing_time": processing_time,
            "operation": operation,
            "task_id": library_task.task_id
        }
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        # Log failed tool call
        if self.mlflow_tracker:
            try:
                self.mlflow_tracker.log_tool_call(
                    agent_id=self.agent_id,
                    tool_name="library",
                    tool_type="library",
                    input_parameters={
                        "operation": operation,
                        "query": query,
                        "data": data,
                        "context": context or {}
                    },
                    output_result=None,
                    processing_time_ms=processing_time,
                    success=False,
                    error_message=str(e),
                    tool_metadata={
                        "operation_type": operation,
                        "error_type": type(e).__name__
                    }
                )
            except Exception as log_e:
                logger.warning(f"Failed to log library error to MLflow: {log_e}")
        
        return {
            "success": False,
            "error": str(e),
            "processing_time": processing_time,
            "operation": operation
        }

# Enhanced delegate_task method:
async def delegate_task(self, task: Task, target_agent_id: str) -> bool:
    """Delegate tasks to other agents with comprehensive tracking."""
    try:
        # Enhanced tracking with detailed context
        if self.mlflow_tracker:
            try:
                self.mlflow_tracker.log_agent_communication(
                    from_agent=self.agent_id,
                    to_agent=target_agent_id,
                    message_type="task_delegation",
                    content={
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "task_description": task.description,
                        "task_priority": task.priority,
                        "task_context": task.context,
                        "delegation_reason": f"Task {task.task_type} delegated to {target_agent_id}",
                        "expected_deliverable": "task_completion"
                    },
                    communication_id=f"delegation_{self.agent_id}_to_{target_agent_id}_{int(time.time())}"
                )
            except Exception as e:
                logger.warning(f"Failed to log task delegation to MLflow: {e}")
        
        # Broadcast delegation event
        await self.agui_broadcaster.broadcast_dialogue_update(
            task_id=self.task_id or "global",
            agent_id=self.agent_id,
            message_id=f"delegation_{int(time.time())}",
            direction="output",
            content={
                "type": "task_delegation",
                "data": {
                    "delegated_task_id": task.task_id,
                    "target_agent": target_agent_id,
                    "task_type": task.task_type,
                    "description": task.description
                },
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "delegation_source": self.agent_id
                }
            },
            sender=self.agent_id
        )
        
        # For now, return True as placeholder (actual delegation to be implemented with team supervisors)
        return True
        
    except Exception as e:
        logger.error(f"Failed to delegate task {task.task_id} to {target_agent_id}: {e}")
        return False

# System prompt logging on initialization:
async def get_system_prompt(self) -> str:
    """Get agent system prompt from YAML configuration with logging."""
    try:
        # Load YAML prompt file
        prompt_file = Path(__file__).parent.parent / "prompts" / f"{self.agent_id}.yaml"
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_config = yaml.safe_load(f)
            
            # Extract system prompt
            system_prompt = prompt_config.get('system_prompt', self._get_default_system_prompt())
            
            # Log system prompt to MLflow for tracking
            if self.mlflow_tracker:
                try:
                    self.mlflow_tracker.log_system_prompt(
                        agent_id=self.agent_id,
                        system_prompt=system_prompt,
                        prompt_source="yaml"
                    )
                except Exception as e:
                    logger.warning(f"Failed to log system prompt to MLflow: {e}")
            
            return system_prompt
        else:
            # Use default prompt and log it
            default_prompt = self._get_default_system_prompt()
            
            if self.mlflow_tracker:
                try:
                    self.mlflow_tracker.log_system_prompt(
                        agent_id=self.agent_id,
                        system_prompt=default_prompt,
                        prompt_source="default"
                    )
                except Exception as e:
                    logger.warning(f"Failed to log default prompt to MLflow: {e}")
            
            return default_prompt
            
    except Exception as e:
        logger.error(f"Failed to load system prompt for {self.agent_id}: {e}")
        return self._get_default_system_prompt()