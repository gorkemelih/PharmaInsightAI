"""File storage service for documents."""

import os
import re
import shutil
from pathlib import Path
from uuid import UUID

# Default upload directory (can be overridden by env var)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/data/uploads")


def sanitize_filename(filename: str) -> str:
    """Remove path traversal characters and dangerous patterns.
    
    Returns a safe filename that can be used for storage.
    """
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")
    # Remove parent directory traversal
    filename = filename.replace("..", "_")
    # Keep only safe characters (alphanumeric, dot, dash, underscore)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Limit length
    return filename[:255] if filename else "unnamed"


def get_document_dir(project_id: UUID, document_id: UUID) -> Path:
    """Get the storage directory for a document."""
    return Path(UPLOAD_DIR) / str(project_id) / str(document_id)


def save_file(
    project_id: UUID,
    document_id: UUID,
    filename: str,
    file_content: bytes,
) -> str:
    """Save uploaded file to disk.
    
    Returns the storage path.
    """
    doc_dir = get_document_dir(project_id, document_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename to prevent path traversal
    safe_filename = sanitize_filename(filename)
    file_path = doc_dir / safe_filename
    file_path.write_bytes(file_content)
    
    return str(file_path)


def get_file_path(storage_path: str) -> Path:
    """Get file path from storage path."""
    return Path(storage_path)


def read_file(storage_path: str) -> bytes:
    """Read file content from storage."""
    path = get_file_path(storage_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {storage_path}")
    return path.read_bytes()


def delete_file(storage_path: str) -> None:
    """Delete a file from storage."""
    path = get_file_path(storage_path)
    if path.exists():
        path.unlink()


def delete_document_dir(project_id: UUID, document_id: UUID) -> None:
    """Delete entire document directory."""
    doc_dir = get_document_dir(project_id, document_id)
    if doc_dir.exists():
        shutil.rmtree(doc_dir)
