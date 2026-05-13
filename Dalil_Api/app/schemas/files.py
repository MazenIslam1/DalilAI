"""
File Upload Schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response after a file is uploaded and processed."""

    dataset_id: str
    filename: str
    file_size_bytes: int
    rows: int
    columns: int
    column_names: list[str]
    message: str = "File uploaded and processed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FileValidationError(BaseModel):
    """Returned when a file fails validation."""

    error: str
    detail: Optional[str] = None
    allowed_extensions: list[str] = [".csv", ".xlsx", ".xls"]
    max_size_mb: int = 100
