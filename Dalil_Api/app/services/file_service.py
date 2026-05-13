"""
File Service
============
Handles file upload, validation, processing, and storage.
"""

import json
from pathlib import Path
from typing import Tuple

import aiofiles
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_logger, get_settings
from app.data.processor import DataProcessor
from app.data.schema_analyzer import SchemaAnalyzer
from app.db.repositories import DatasetRepository
from app.schemas.datasets import DatasetSchema
from app.schemas.files import FileUploadResponse
from app.utils.file_utils import (
    cleanup_temp_file,
    get_temp_filepath,
    validate_file_extension,
    validate_file_size,
)
from app.utils.helpers import generate_id

logger = get_logger(__name__)
settings = get_settings()


class FileService:
    """Orchestrates file upload, validation, and processing."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dataset_repo = DatasetRepository(db)

    async def upload_and_process(self, file: UploadFile) -> FileUploadResponse:
        """
        Full file upload pipeline:
        1. Validate extension and size
        2. Save to temp location
        3. Read into Polars DataFrame
        4. Analyze schema
        5. Cache as Parquet
        6. Store metadata in database
        7. Cleanup temp file
        """
        # ── Validate ────────────────────────────────────────────
        valid_ext, ext_error = validate_file_extension(file.filename)
        if not valid_ext:
            raise ValueError(ext_error)

        # Read file content
        content = await file.read()
        valid_size, size_error = validate_file_size(len(content))
        if not valid_size:
            raise ValueError(size_error)

        # ── Save to temp ────────────────────────────────────────
        temp_path = get_temp_filepath(file.filename)
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)

        logger.info("file_saved", path=str(temp_path), size=len(content))

        try:
            # ── Process ─────────────────────────────────────────
            dataset_id = generate_id()

            # Run CPU-bound processing in threadpool
            df, parquet_path = await run_in_threadpool(
                DataProcessor.ingest_file, temp_path, dataset_id
            )

            # ── Analyze Schema ──────────────────────────────────
            schema = await run_in_threadpool(
                SchemaAnalyzer.analyze, df, dataset_id, file.filename
            )

            # ── Store in DB ─────────────────────────────────────
            dataset = await self.dataset_repo.create(
                id=dataset_id,
                filename=file.filename,
                original_path=str(temp_path),
                parquet_path=str(parquet_path),
                row_count=df.height,
                column_count=df.width,
                file_size_bytes=len(content),
                schema_json=json.dumps(schema.model_dump(), default=str),
            )

            logger.info(
                "file_processed",
                dataset_id=dataset_id,
                rows=df.height,
                columns=df.width,
            )

            return FileUploadResponse(
                dataset_id=dataset_id,
                filename=file.filename,
                file_size_bytes=len(content),
                rows=df.height,
                columns=df.width,
                column_names=df.columns,
            )

        finally:
            # ── Cleanup temp file ───────────────────────────────
            cleanup_temp_file(temp_path)
