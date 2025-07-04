"""
MLflow Chat Tracking for ATLAS
Comprehensive tracking of chat conversations and message interactions
"""

import json
import mlflow
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .enhanced_tracking import EnhancedATLASTracker

class ChatTrackingManager:
    """
    Manages MLflow tracking for chat conversations
    Creates experiments per chat session and tracks all interactions
    """
    
    def __init__(self, enhanced_tracker: Optional[EnhancedATLASTracker] = None):
        self.enhanced_tracker = enhanced_tracker or EnhancedATLASTracker()
        self.chat_experiments = {}  # session_id -> experiment_id
        self.chat_runs = {}  # session_id -> run_id
        
    async def create_chat_experiment(
        self, 
        session_id: str, 
        task_id: str,
        chat_metadata: Dict[str, Any]
    ) -> str:
        """
        Create MLflow experiment for a chat session
        Returns MLflow run ID
        """
        try:
            # Create experiment name based on task and session
            experiment_name = f"atlas_chat_{task_id}_{session_id[:8]}"
            
            # Try to get existing experiment or create new one
            try:
                experiment = mlflow.get_experiment_by_name(experiment_name)
                experiment_id = experiment.experiment_id if experiment else None
            except Exception:
                experiment_id = None
                
            if not experiment_id:
                experiment_id = mlflow.create_experiment(
                    name=experiment_name,
                    tags={
                        "type": "chat_session",
                        "task_id": task_id,
                        "session_id": session_id,
                        "created_at": datetime.now().isoformat()
                    }
                )
            
            self.chat_experiments[session_id] = experiment_id
            
            # Start a run for this chat session
            with mlflow.start_run(experiment_id=experiment_id, run_name=f"chat_{session_id[:8]}") as run:
                run_id = run.info.run_id
                self.chat_runs[session_id] = run_id
                
                # Log initial chat metadata
                mlflow.log_params({
                    "session_id": session_id,
                    "task_id": task_id,
                    "user_id": chat_metadata.get("user_id", "default_user"),
                    "chat_type": "interactive",
                    "tracking_version": "1.0"
                })
                
                # Log initial metrics
                mlflow.log_metrics({
                    "message_count": 0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0,
                    "session_start_time": datetime.now().timestamp()
                })
                
                # Log session metadata as artifact
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(chat_metadata, f, indent=2)
                    temp_path = f.name
                
                mlflow.log_artifact(temp_path, "session_metadata.json")
                Path(temp_path).unlink()  # Clean up temp file
                
            return run_id
            
        except Exception as e:
            print(f"Error creating chat experiment: {e}")
            return None
    
    async def track_message(
        self,
        session_id: str,
        message_data: Dict[str, Any]
    ):
        """
        Track individual message in MLflow
        """
        try:
            run_id = self.chat_runs.get(session_id)
            if not run_id:
                print(f"No MLflow run found for session {session_id}")
                return
            
            with mlflow.start_run(run_id=run_id):
                # Track message as event/metric
                message_type = message_data.get("message_type", "unknown")
                tokens_used = message_data.get("tokens_used", 0)
                cost_usd = message_data.get("cost_usd", 0.0)
                processing_time = message_data.get("processing_time_ms", 0)
                
                # Log message metrics
                timestamp = datetime.now().timestamp()
                mlflow.log_metric(f"message_{message_type}_count", 1, step=int(timestamp))
                mlflow.log_metric("tokens_per_message", tokens_used, step=int(timestamp))
                mlflow.log_metric("cost_per_message", cost_usd, step=int(timestamp))
                
                if processing_time > 0:
                    mlflow.log_metric("processing_time_ms", processing_time, step=int(timestamp))
                
                # Update cumulative metrics
                current_run = mlflow.get_run(run_id)
                current_tokens = current_run.data.metrics.get("total_tokens", 0)
                current_cost = current_run.data.metrics.get("total_cost_usd", 0.0)
                current_count = current_run.data.metrics.get("message_count", 0)
                
                mlflow.log_metrics({
                    "total_tokens": current_tokens + tokens_used,
                    "total_cost_usd": current_cost + cost_usd,
                    "message_count": current_count + 1
                })
                
                # Log model usage if available
                model_used = message_data.get("model_used")
                if model_used:
                    mlflow.log_param(f"last_model_used", model_used)
                
                # Track response quality if available
                quality = message_data.get("response_quality")
                if quality is not None:
                    mlflow.log_metric("response_quality", quality, step=int(timestamp))
                
        except Exception as e:
            print(f"Error tracking message: {e}")
    
    async def store_conversation_artifact(
        self,
        session_id: str,
        conversation: List[Dict[str, Any]]
    ):
        """
        Store complete conversation as MLflow artifact
        """
        try:
            run_id = self.chat_runs.get(session_id)
            if not run_id:
                print(f"No MLflow run found for session {session_id}")
                return
            
            with mlflow.start_run(run_id=run_id):
                # Create conversation artifact
                conversation_data = {
                    "session_id": session_id,
                    "exported_at": datetime.now().isoformat(),
                    "message_count": len(conversation),
                    "conversation": conversation
                }
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(conversation_data, f, indent=2, default=str)
                    temp_path = f.name
                
                mlflow.log_artifact(temp_path, "conversation_history.json")
                Path(temp_path).unlink()  # Clean up temp file
                
                # Also create a text version for readability
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(f"ATLAS Chat Conversation - Session {session_id}\n")
                    f.write(f"Exported: {datetime.now().isoformat()}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for msg in conversation:
                        timestamp = msg.get("timestamp", "unknown")
                        msg_type = msg.get("message_type", "unknown")
                        agent_id = msg.get("agent_id", "system")
                        content = msg.get("content", "")
                        
                        f.write(f"[{timestamp}] {msg_type.upper()}")
                        if agent_id != "system":
                            f.write(f" ({agent_id})")
                        f.write(f":\n{content}\n\n")
                    
                    temp_text_path = f.name
                
                mlflow.log_artifact(temp_text_path, "conversation_readable.txt")
                Path(temp_text_path).unlink()  # Clean up temp file
                
        except Exception as e:
            print(f"Error storing conversation artifact: {e}")
    
    async def update_chat_metrics(
        self,
        session_id: str,
        metrics: Dict[str, Any]
    ):
        """
        Update chat session metrics in MLflow
        """
        try:
            run_id = self.chat_runs.get(session_id)
            if not run_id:
                print(f"No MLflow run found for session {session_id}")
                return
            
            with mlflow.start_run(run_id=run_id):
                # Update metrics
                mlflow.log_metrics(metrics)
                
                # Log session duration if session is completed
                if metrics.get("session_completed"):
                    start_time = metrics.get("session_start_time")
                    if start_time:
                        duration = datetime.now().timestamp() - start_time
                        mlflow.log_metric("session_duration_seconds", duration)
                
        except Exception as e:
            print(f"Error updating chat metrics: {e}")
    
    async def finalize_chat_session(
        self,
        session_id: str,
        final_conversation: List[Dict[str, Any]],
        session_stats: Dict[str, Any]
    ):
        """
        Finalize chat session tracking
        """
        try:
            # Store final conversation
            await self.store_conversation_artifact(session_id, final_conversation)
            
            # Update final metrics
            final_metrics = {
                "session_completed": True,
                "final_message_count": len(final_conversation),
                "session_end_time": datetime.now().timestamp(),
                **session_stats
            }
            
            await self.update_chat_metrics(session_id, final_metrics)
            
            # End the MLflow run
            run_id = self.chat_runs.get(session_id)
            if run_id:
                with mlflow.start_run(run_id=run_id):
                    mlflow.end_run()
                
                # Clean up tracking state
                self.chat_runs.pop(session_id, None)
                self.chat_experiments.pop(session_id, None)
                
        except Exception as e:
            print(f"Error finalizing chat session: {e}")
    
    async def get_chat_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get analytics for a chat session from MLflow
        """
        try:
            run_id = self.chat_runs.get(session_id)
            if not run_id:
                return {}
            
            run = mlflow.get_run(run_id)
            return {
                "run_id": run_id,
                "metrics": run.data.metrics,
                "params": run.data.params,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time
            }
            
        except Exception as e:
            print(f"Error getting chat analytics: {e}")
            return {}

# Global instance for use across the application
chat_tracker = ChatTrackingManager()