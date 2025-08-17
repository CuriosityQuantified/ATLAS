"""
Configuration management for ATLAS Backend
Loads settings from environment variables with sensible defaults
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "atlas_main"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "atlas_password"
    
    # Atlas Agents Database Configuration
    ATLAS_AGENTS_USER: str = "atlas_agents_user"
    ATLAS_AGENTS_PASSWORD: str = "atlas_agents_password"
    
    # Redis Configuration  
    REDIS_URL: str = "redis://localhost:6379"
    
    # MLflow Configuration
    MLFLOW_TRACKING_URI: str = "http://localhost:5002"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Keys (optional)
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra environment variables

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get global settings instance (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings