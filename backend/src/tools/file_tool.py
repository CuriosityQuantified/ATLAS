"""
File Operations Tool for ATLAS Agents
Session-scoped file operations - all files automatically organized by chat session
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Base directory for agent outputs (configurable)
BASE_OUTPUT_DIR = Path(os.getenv("ATLAS_OUTPUT_DIR", "/Users/nicholaspate/Documents/01_Active/ATLAS/outputs"))

# Global session path - initialized when user starts new chat
_session_path: Optional[Path] = None

def initialize_session(session_id: Optional[str] = None) -> str:
    """
    Initialize session directory when user starts a new chat.
    Called by the backend API when processing the first message.

    Args:
        session_id: Optional session identifier (defaults to timestamp)

    Returns:
        Path to the created session directory
    """
    global _session_path

    # Create session directory
    if session_id:
        _session_path = BASE_OUTPUT_DIR / f"session_{session_id}"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _session_path = BASE_OUTPUT_DIR / f"session_{timestamp}"

    # Create standard subdirectories
    subdirs = ["research", "analysis", "reports", "data"]
    for subdir in subdirs:
        (_session_path / subdir).mkdir(parents=True, exist_ok=True)

    # Create session metadata
    metadata = {
        "session_id": session_id or timestamp,
        "created_at": datetime.now().isoformat(),
        "directories": subdirs
    }

    metadata_path = _session_path / "session.meta.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return str(_session_path)

def get_session_path() -> Path:
    """
    Get the current session path.
    Raises error if session not initialized.
    """
    if _session_path is None:
        raise RuntimeError("Session not initialized. Backend must call initialize_session() first.")
    return _session_path

def save_output(
    filename: str,
    content: str,
    file_type: str = "text",
    subdirectory: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Save content to a file in the session directory.

    Args:
        filename: Name of the file to create
        content: Content to write
        file_type: Type of file (text/json/markdown/yaml)
        subdirectory: Optional subdirectory within session (research/analysis/reports/data)
        metadata: Optional metadata about the file

    Returns:
        Information about the created file
    """
    session_dir = get_session_path()

    # Determine output directory
    if subdirectory:
        output_dir = session_dir / subdirectory
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = session_dir

    # Add appropriate extension if not present
    extensions = {
        "text": ".txt",
        "json": ".json",
        "markdown": ".md",
        "yaml": ".yaml"
    }
    if not any(filename.endswith(ext) for ext in extensions.values()):
        filename = filename + extensions.get(file_type, ".txt")

    file_path = output_dir / filename

    try:
        # Write the content
        if file_type == "json" and isinstance(content, (dict, list)):
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
        else:
            with open(file_path, 'w') as f:
                f.write(content)

        # Create metadata file if provided
        if metadata:
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta.json')
            metadata["created_at"] = datetime.now().isoformat()
            metadata["file_path"] = str(file_path)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

        return {
            "status": "success",
            "file_path": str(file_path),
            "size": file_path.stat().st_size,
            "created_at": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def load_file(
    filename: str,
    subdirectory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load content from a file in the session directory.

    Args:
        filename: Name of the file to read
        subdirectory: Optional subdirectory within session

    Returns:
        File content and metadata
    """
    session_dir = get_session_path()

    # Determine file path
    if subdirectory:
        file_path = session_dir / subdirectory / filename
    else:
        # Search for file in session root and all subdirectories
        file_path = session_dir / filename
        if not file_path.exists():
            # Try to find in subdirectories
            for subdir in ["research", "analysis", "reports", "data"]:
                potential_path = session_dir / subdir / filename
                if potential_path.exists():
                    file_path = potential_path
                    break

    try:
        if not file_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {filename}"
            }

        with open(file_path, 'r') as f:
            content = f.read()

        # Check for metadata file
        metadata_path = Path(str(file_path) + '.meta.json')
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        return {
            "status": "success",
            "content": content,
            "file_path": str(file_path),
            "size": file_path.stat().st_size,
            "metadata": metadata
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def list_outputs(
    subdirectory: Optional[str] = None,
    file_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all files in the session directory.

    Args:
        subdirectory: Optional filter by subdirectory
        file_type: Optional filter by file type

    Returns:
        List of file information
    """
    session_dir = get_session_path()

    # Determine search directory
    if subdirectory:
        search_dir = session_dir / subdirectory
    else:
        search_dir = session_dir

    if not search_dir.exists():
        return []

    files = []
    pattern = "*"
    if file_type:
        extensions = {
            "text": "*.txt",
            "json": "*.json",
            "markdown": "*.md",
            "yaml": "*.yaml"
        }
        pattern = extensions.get(file_type, "*")

    # Use rglob for recursive search if no subdirectory specified
    glob_method = search_dir.rglob if not subdirectory else search_dir.glob
    for file_path in glob_method(pattern):
        # Skip metadata files and directories
        if '.meta.json' in file_path.name or file_path.is_dir():
            continue

        # Get relative path from session directory
        relative_path = file_path.relative_to(session_dir)

        files.append({
            "filename": file_path.name,
            "relative_path": str(relative_path),
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        })

    return sorted(files, key=lambda x: x['modified'], reverse=True)

def append_content(
    filename: str,
    content: str,
    subdirectory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Append content to an existing file in the session directory.

    Args:
        filename: Name of the file to append to
        content: Content to append
        subdirectory: Optional subdirectory within session

    Returns:
        Status information
    """
    session_dir = get_session_path()

    # Determine file path
    if subdirectory:
        file_path = session_dir / subdirectory / filename
    else:
        file_path = session_dir / filename

    try:
        if not file_path.exists():
            # Create the file if it doesn't exist
            return save_output(filename, content, subdirectory=subdirectory)

        with open(file_path, 'a') as f:
            f.write('\n' + content)

        return {
            "status": "success",
            "file_path": str(file_path),
            "new_size": file_path.stat().st_size,
            "appended_at": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }