
import os
from dataclasses import dataclass

@dataclass
class MLflowConfig:
    """
    Configuration for the MLflow Tracking Server connection.
    
    Attributes:
        tracking_uri (str): The full URL to the MLflow tracking server.
        artifact_root (str): The S3 path for storing artifacts.
    """
    tracking_uri: str
    artifact_root: str

def get_mlflow_config() -> MLflowConfig:
    """
    Initializes and returns the MLflowConfig from environment variables.
    """
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    artifact_root = os.getenv("MLFLOW_ARTIFACT_URI", "s3://mlflow-artifacts")
    
    if not tracking_uri:
        raise ValueError("MLFLOW_TRACKING_URI environment variable not set.")
        
    if not artifact_root:
        raise ValueError("MLFLOW_ARTIFACT_URI environment variable not set.")

    return MLflowConfig(tracking_uri=tracking_uri, artifact_root=artifact_root)

