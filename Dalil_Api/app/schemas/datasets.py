"""
Dataset Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """Schema information for a single column."""

    name: str
    dtype: str
    nullable: bool = True
    unique_count: Optional[int] = None
    sample_values: List[Any] = Field(default_factory=list)
    stats: Optional[Dict[str, Any]] = None  # min, max, mean for numeric


class DatasetSchema(BaseModel):
    """Full schema of a dataset."""

    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    columns: List[ColumnInfo]
    file_size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DatasetListItem(BaseModel):
    """Summary item for listing datasets."""

    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    file_size_bytes: int
    created_at: datetime


class DatasetDetail(BaseModel):
    """Full dataset detail including schema."""

    dataset_id: str
    filename: str
    schema_info: DatasetSchema
    sample_data: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
