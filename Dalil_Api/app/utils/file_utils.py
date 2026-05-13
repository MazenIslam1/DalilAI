"""
File Validation & Security Utilities
=====================================
Validates uploads and protects against CSV injection and malicious files.
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple

from app.config import get_settings

settings = get_settings()

# Characters that can trigger formula injection in Excel/CSV
INJECTION_PATTERNS = re.compile(r"^[=+\-@\t\r]")


def validate_file_extension(filename: str) -> Tuple[bool, Optional[str]]:
    """Check if the file extension is allowed."""
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_ext_list:
        return False, f"Extension '{ext}' not allowed. Allowed: {settings.allowed_ext_list}"
    return True, None


def validate_file_size(size_bytes: int) -> Tuple[bool, Optional[str]]:
    """Check if file size is within limits."""
    if size_bytes > settings.max_upload_bytes:
        return False, f"File too large ({size_bytes / 1024 / 1024:.1f}MB). Max: {settings.MAX_UPLOAD_SIZE_MB}MB"
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from filename.
    Preserves extension but strips everything except alphanumeric, dash, underscore, dot.
    """
    # Keep only safe characters
    safe_name = re.sub(r"[^\w\-.]", "_", filename)
    # Prevent directory traversal
    safe_name = safe_name.replace("..", "_")
    return safe_name


def sanitize_cell_value(value: str) -> str:
    """
    Protect against CSV/Excel formula injection.
    Strips leading characters that could be interpreted as formulas.
    """
    if isinstance(value, str) and INJECTION_PATTERNS.match(value):
        return "'" + value  # Prefix with single quote to neutralize
    return value


def get_temp_filepath(filename: str) -> Path:
    """Generate a secure temporary file path in the upload directory."""
    safe_name = sanitize_filename(filename)
    filepath = settings.upload_path / safe_name

    # Avoid overwriting existing files
    counter = 1
    stem = filepath.stem
    suffix = filepath.suffix
    while filepath.exists():
        filepath = settings.upload_path / f"{stem}_{counter}{suffix}"
        counter += 1

    return filepath


def cleanup_temp_file(filepath: Path) -> None:
    """Safely remove a temporary file."""
    try:
        if filepath.exists():
            filepath.unlink()
    except OSError:
        pass  # Log but don't crash
