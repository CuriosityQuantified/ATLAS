# SNAPSHOT: Changes made to backend/src/api/agent_endpoints.py for MLflow integration

# Key changes made:
# 1. Initialize EnhancedATLASTracker for each task
# 2. Pass mlflow_tracker to agent initialization
# 3. Enhanced error handling and run management
# 4. Return MLflow run information in API responses

# Modified task creation endpoint:
@router.post("/tasks", response_model=TaskCreationResponse)
async def create_agent_task(task_request: TaskRequest):
    """Create a new agent task with Enhanced MLflow tracking."""
    
    task_id = f"task_{int(time.time())}_{task_request.task_type}"
    
    # Initialize Enhanced MLflow Tracker for this task
    mlflow_tracker = None
    experiment_name = f"ATLAS_Task_{task_id}"
    
    try:
        from backend.src.mlflow.enhanced_tracking import EnhancedATLASTracker
        
        mlflow_tracker = EnhancedATLASTracker(
            tracking_uri="http://localhost:5002",
            experiment_name=experiment_name,
            auto_start_run=True,
            enable_detailed_logging=True
        )
        
        logger.info(f"Enhanced MLflow tracker initialized for task {task_id}")
        
    except Exception as e:
        logger.warning(f"Failed to initialize MLflow tracker: {e}")
        # Continue without MLflow tracking
    
    try:
        # Initialize AG-UI Event Broadcaster
        broadcaster = AGUIEventBroadcaster(connection_manager=connection_manager)
        
        # Initialize Global Supervisor with enhanced tracking
        global_supervisor = GlobalSupervisorAgent(
            task_id=task_id,
            agui_broadcaster=broadcaster,
            mlflow_tracker=mlflow_tracker  # Pass enhanced tracker
        )
        
        # Initialize Library Agent with enhanced tracking  
        library_agent = LibraryAgent(
            task_id=task_id,
            agui_broadcaster=broadcaster,
            mlflow_tracker=mlflow_tracker  # Pass enhanced tracker
        )
        
        # Store agents globally for task management
        active_tasks[task_id] = {
            "task_request": task_request,
            "global_supervisor": global_supervisor,
            "library_agent": library_agent,
            "mlflow_tracker": mlflow_tracker,
            "created_at": datetime.now(),
            "status": "created"
        }
        
        # Get MLflow run information
        mlflow_run_id = None
        mlflow_url = None
        
        if mlflow_tracker and mlflow_tracker.current_run_id:
            mlflow_run_id = mlflow_tracker.current_run_id
            mlflow_url = mlflow_tracker.get_current_run_url()
            
            # Log task creation parameters
            try:
                mlflow_tracker.log_task_assignment(
                    task_id=task_id,
                    task_type=task_request.task_type,
                    assigned_agent="global_supervisor",
                    task_data={
                        "description": task_request.description,
                        "priority": task_request.priority,
                        "context": task_request.context
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log task assignment: {e}")
        
        return TaskCreationResponse(
            task_id=task_id,
            status="created",
            message=f"Task created successfully with Enhanced MLflow tracking",
            agent_assignments={
                "global_supervisor": "Orchestrating task execution",
                "library_agent": "Knowledge management ready"
            },
            mlflow_run_id=mlflow_run_id,
            mlflow_url=mlflow_url
        )
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        
        # Clean up MLflow run on error
        if mlflow_tracker:
            try:
                mlflow_tracker.cleanup()
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Task creation failed: {str(e)}"
        )

# Modified task start endpoint:
@router.post("/tasks/{task_id}/start", response_model=TaskStartResponse)
async def start_agent_task(task_id: str):
    """Start processing an agent task with enhanced tracking."""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = active_tasks[task_id]
    task_request = task_info["task_request"]
    global_supervisor = task_info["global_supervisor"]
    mlflow_tracker = task_info["mlflow_tracker"]
    
    try:
        # Update task status
        task_info["status"] = "processing"
        task_info["started_at"] = datetime.now()
        
        # Create Task object for processing
        task = Task(
            task_id=task_id,
            task_type=task_request.task_type,
            description=task_request.description,
            priority=task_request.priority,
            context=task_request.context,
            assigned_to="global_supervisor"
        )
        
        # Start task processing (async)
        asyncio.create_task(process_task_async(task, global_supervisor, mlflow_tracker))
        
        return TaskStartResponse(
            task_id=task_id,
            status="processing",
            message="Task processing started",
            started_at=task_info["started_at"],
            estimated_completion=None
        )
        
    except Exception as e:
        logger.error(f"Failed to start task {task_id}: {e}")
        task_info["status"] = "failed"
        
        raise HTTPException(
            status_code=500,
            detail=f"Task start failed: {str(e)}"
        )

# Enhanced task processing function:
async def process_task_async(task: Task, global_supervisor: GlobalSupervisorAgent, mlflow_tracker):
    """Process task asynchronously with enhanced tracking."""
    try:
        # Log task start
        if mlflow_tracker:
            try:
                mlflow_tracker.log_agent_status_change(
                    agent_id=global_supervisor.agent_id,
                    old_status="idle",
                    new_status="processing",
                    reason=f"Starting task processing: {task.task_type}",
                    context={
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "description": task.description
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log task start: {e}")
        
        # Process the task
        result = await global_supervisor.process_task(task)
        
        # Update task status
        if task.task_id in active_tasks:
            active_tasks[task.task_id]["status"] = "completed" if result.success else "failed"
            active_tasks[task.task_id]["completed_at"] = datetime.now()
            active_tasks[task.task_id]["result"] = result
        
        # Log task completion
        if mlflow_tracker:
            try:
                mlflow_tracker.log_task_completion(
                    task_id=task.task_id,
                    success=result.success,
                    result=asdict(result) if result else None,
                    processing_time=result.processing_time if result else None
                )
                
                mlflow_tracker.log_agent_status_change(
                    agent_id=global_supervisor.agent_id,
                    old_status="processing",
                    new_status="completed" if result.success else "error",
                    reason=f"Task completed: {result.success}",
                    context={
                        "task_id": task.task_id,
                        "success": result.success,
                        "processing_time": result.processing_time if result else None
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log task completion: {e}")
        
        logger.info(f"Task {task.task_id} completed: {result.success}")
        
    except Exception as e:
        logger.error(f"Task processing failed for {task.task_id}: {e}")
        
        # Update task status on error
        if task.task_id in active_tasks:
            active_tasks[task.task_id]["status"] = "failed"
            active_tasks[task.task_id]["error"] = str(e)
        
        # Log task failure
        if mlflow_tracker:
            try:
                mlflow_tracker.log_agent_status_change(
                    agent_id=global_supervisor.agent_id,
                    old_status="processing",
                    new_status="error",
                    reason=f"Task failed: {str(e)}",
                    context={
                        "task_id": task.task_id,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
            except Exception as log_e:
                logger.warning(f"Failed to log task failure: {log_e}")

# Import statement changes:
from backend.src.mlflow.enhanced_tracking import EnhancedATLASTracker
from backend.src.agents.global_supervisor import GlobalSupervisorAgent
from backend.src.agents.library import LibraryAgent
from backend.src.agui.handlers import AGUIEventBroadcaster
from backend.src.agents.base import Task
from dataclasses import asdict