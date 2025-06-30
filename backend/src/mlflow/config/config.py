"""
MLflow Configuration for ATLAS

Provides configuration management for MLflow tracking URI and related settings.
"""

import os
from typing import Optional

class MLflowConfig:
    """Configuration class for MLflow tracking settings."""
    
    def __init__(self, tracking_uri: Optional[str] = None):
        """
        Initialize MLflow configuration.
        
        Args:
            tracking_uri: Optional override for MLflow tracking URI.
                         If not provided, uses environment variable or default.
        """
        self.tracking_uri = tracking_uri or self._get_tracking_uri()
        self.artifact_root = self._get_artifact_root()
        self.backend_store_uri = self._get_backend_store_uri()
    
    def _get_tracking_uri(self) -> str:
        """Get MLflow tracking URI from environment or use default."""
        return os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    
    def _get_artifact_root(self) -> str:
        """Get artifact storage root from environment or use default."""
        return os.getenv('MLFLOW_ARTIFACT_ROOT', 's3://mlflow-artifacts')
    
    def _get_backend_store_uri(self) -> str:
        """Get backend store URI from environment or use default."""
        return os.getenv('MLFLOW_BACKEND_STORE_URI', 'sqlite:///mlflow.db')
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary for logging/debugging."""
        return {
            'tracking_uri': self.tracking_uri,
            'artifact_root': self.artifact_root,
            'backend_store_uri': self.backend_store_uri
        }