"""File storage service for documents with security hardening."""

import os
import re
import shutil
from pathlib import Path
from uuid import UUID

# Default upload directory (can be overridden by env var)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))

# Magic bytes for allowed file types
MAGIC_BYTES = {
    "pdf": b"%PDF",
    "txt": None,  # Text files don't have magic bytes
    "md": None,
    "markdown": None,
    "csv": None,
}


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


def validate_magic_bytes(filename: str, content: bytes) -> bool:
    """Validate file content matches expected magic bytes.
    
    Returns True if valid, raises ValueError if invalid.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    expected_magic = MAGIC_BYTES.get(ext)
    
    if expected_magic is None:
        # No magic byte validation for text-based formats
        return True
    
    if not content.startswith(expected_magic):
        raise ValueError(
            f"File content does not match expected format for .{ext} files. "
            "The file may be corrupted or misnamed."
        )
    
    return True


def get_document_dir(tenant_id: UUID, project_id: UUID, document_id: UUID) -> Path:
    """Get the storage directory for a document.
    
    Path structure: UPLOAD_DIR/tenant_id/project_id/document_id
    This ensures per-tenant isolation.
    """
    return UPLOAD_DIR / str(tenant_id) / str(project_id) / str(document_id)


def validate_path_within_upload_dir(path: Path) -> bool:
    """Ensure path is within UPLOAD_DIR to prevent path traversal attacks.
    
    Raises ValueError if path escapes upload directory.
    """
    try:
        # Resolve to absolute path (follows symlinks, resolves ..)
        resolved_path = path.resolve()
        upload_dir_resolved = UPLOAD_DIR.resolve()
        
        # Check if the resolved path is under upload dir
        resolved_path.relative_to(upload_dir_resolved)
        return True
    except ValueError:
        raise ValueError(
            f"Path traversal detected: {path} is outside allowed storage directory"
        )


def save_file(
    tenant_id: UUID,
    project_id: UUID,
    document_id: UUID,
    filename: str,
    file_content: bytes,
) -> str:
    """Save uploaded file to disk with security validation.
    
    Args:
        tenant_id: Tenant UUID for isolation
        project_id: Project UUID
        document_id: Document UUID
        filename: Original filename (will be sanitized)
        file_content: File bytes
        
    Returns:
        Storage path string
        
    Raises:
        ValueError: If file content doesn't match expected magic bytes
    """
    # Validate magic bytes for known file types
    validate_magic_bytes(filename, file_content)
    
    # Get tenant-isolated directory
    doc_dir = get_document_dir(tenant_id, project_id, document_id)
    
    # Validate path is within upload directory
    validate_path_within_upload_dir(doc_dir)
    
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename to prevent path traversal
    safe_filename = sanitize_filename(filename)
    file_path = doc_dir / safe_filename
    
    # Final validation before write
    validate_path_within_upload_dir(file_path)
    
    file_path.write_bytes(file_content)
    
    return str(file_path)


def get_file_path(storage_path: str) -> Path:
    """Get validated file path from storage path.
    
    Raises ValueError if path is outside upload directory.
    """
    path = Path(storage_path)
    validate_path_within_upload_dir(path)
    return path


def read_file(storage_path: str) -> bytes:
    """Read file content from storage with path validation.
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If path escapes upload directory
    """
    path = get_file_path(storage_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {storage_path}")
    return path.read_bytes()


def delete_file(storage_path: str) -> None:
    """Delete a file from storage with path validation."""
    path = get_file_path(storage_path)
    if path.exists():
        path.unlink()


def delete_document_dir(tenant_id: UUID, project_id: UUID, document_id: UUID) -> None:
    """Delete entire document directory."""
    doc_dir = get_document_dir(tenant_id, project_id, document_id)
    
    # Validate before deletion
    validate_path_within_upload_dir(doc_dir)
    
    if doc_dir.exists():
        shutil.rmtree(doc_dir)
