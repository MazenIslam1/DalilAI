"""
Dataset Service
===============
Manages dataset metadata, listing, and deletion.
"""

import json
from typing import List, Optional

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_logger
from app.data.processor import DataProcessor
from app.data.sampler import DataSampler
from app.data.schema_analyzer import SchemaAnalyzer
from app.db.repositories import DatasetRepository
from app.schemas.datasets import DatasetDetail, DatasetListItem, DatasetSchema
from app.utils.file_utils import cleanup_temp_file
from pathlib import Path

logger = get_logger(__name__)


class DatasetService:
    """CRUD and metadata operations for datasets."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dataset_repo = DatasetRepository(db)

    async def list_datasets(self) -> List[DatasetListItem]:
        """List all uploaded datasets."""
        datasets = await self.dataset_repo.list_all()
        return [
            DatasetListItem(
                dataset_id=d.id,
                filename=d.filename,
                row_count=d.row_count,
                column_count=d.column_count,
                file_size_bytes=d.file_size_bytes,
                created_at=d.created_at,
            )
            for d in datasets
        ]

    async def get_dataset_detail(self, dataset_id: str) -> Optional[DatasetDetail]:
        """Get full dataset details including schema and sample data."""
        dataset = await self.dataset_repo.get(dataset_id)
        if not dataset:
            return None

        # Parse schema
        schema = None
        if dataset.schema_json:
            try:
                schema_data = json.loads(dataset.schema_json)
                schema = DatasetSchema(**schema_data)
            except Exception:
                pass

        # Get sample data
        sample_data = []
        df = await run_in_threadpool(DataProcessor.load_parquet, dataset_id)
        if df is not None:
            sample_rows = df.head(5).to_dicts()
            sample_data = [{k: str(v) for k, v in row.items()} for row in sample_rows]

        if schema is None:
            schema = DatasetSchema(
                dataset_id=dataset_id,
                filename=dataset.filename,
                row_count=dataset.row_count,
                column_count=dataset.column_count,
                columns=[],
                file_size_bytes=dataset.file_size_bytes,
            )

        return DatasetDetail(
            dataset_id=dataset.id,
            filename=dataset.filename,
            schema_info=schema,
            sample_data=sample_data,
            created_at=dataset.created_at,
        )

    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset and its cached files."""
        dataset = await self.dataset_repo.get(dataset_id)
        if not dataset:
            return False

        # Cleanup Parquet cache
        if dataset.parquet_path:
            cleanup_temp_file(Path(dataset.parquet_path))

        # Delete from DB
        await self.dataset_repo.delete(dataset_id)
        logger.info("dataset_deleted", dataset_id=dataset_id)
        return True
