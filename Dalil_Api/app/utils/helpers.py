"""
General Helper Utilities
"""

import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def hash_query(query: str, dataset_id: str) -> str:
    """Create a cache key from query + dataset."""
    raw = f"{dataset_id}:{query.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def format_file_size(size_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def safe_dict(obj: Any) -> Dict:
    """Safely convert an object to a JSON-serializable dict."""
    if isinstance(obj, dict):
        return {k: safe_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_dict(i) for i in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    return str(obj)
