"""
Checkpointer configuration for LangGraph state persistence.
Supports both SQLite (development) and PostgreSQL (production).
"""

import os
from typing import Optional
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver


def get_checkpointer(checkpointer_type: Optional[str] = None):
    """
    Get appropriate checkpointer based on environment or explicit type.
    
    Args:
        checkpointer_type: Optional explicit type ('sqlite', 'postgres', or None for auto-detect)
    
    Returns:
        Checkpointer instance or None if checkpointing is disabled
    """
    # Check if checkpointing is disabled
    if os.getenv("DISABLE_CHECKPOINTING", "false").lower() == "true":
        return None
    
    # Determine checkpointer type
    if checkpointer_type:
        selected_type = checkpointer_type
    elif os.getenv("POSTGRES_URL"):
        selected_type = "postgres"
    else:
        selected_type = "sqlite"
    
    # Create appropriate checkpointer
    if selected_type == "postgres":
        postgres_url = os.getenv("POSTGRES_URL")
        if not postgres_url:
            raise ValueError("POSTGRES_URL environment variable required for PostgreSQL checkpointer")
        
        try:
            # Create PostgreSQL checkpointer
            return PostgresSaver.from_conn_string(postgres_url)
        except Exception as e:
            print(f"Failed to create PostgreSQL checkpointer: {e}")
            print("Falling back to SQLite checkpointer")
            selected_type = "sqlite"
    
    if selected_type == "sqlite":
        # Get database path from environment or use default
        db_path = os.getenv("SQLITE_DB_PATH", "deepagents.db")
        
        try:
            # Create SQLite checkpointer
            return SqliteSaver.from_conn_string(db_path)
        except Exception as e:
            print(f"Failed to create SQLite checkpointer: {e}")
            return None
    
    return None


def setup_checkpointer_tables(checkpointer):
    """
    Setup necessary tables for the checkpointer.
    This is called automatically by most checkpointers, but can be called manually if needed.
    
    Args:
        checkpointer: The checkpointer instance
    """
    if checkpointer and hasattr(checkpointer, 'setup'):
        try:
            checkpointer.setup()
            print(f"Checkpointer tables setup successfully for {type(checkpointer).__name__}")
        except Exception as e:
            print(f"Failed to setup checkpointer tables: {e}")