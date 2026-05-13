"""
Datasets Router
===============
Endpoints for managing uploaded datasets.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.middleware.auth import verify_api_key
from app.middleware.rate_limiter import limiter
from app.schemas.datasets import DatasetDetail, DatasetListItem
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.get(
    "/",
    response_model=List[DatasetListItem],
    summary="List all uploaded datasets",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("30/minute")
async def list_datasets(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List all datasets that have been uploaded and processed."""
    service = DatasetService(db)
    return await service.list_datasets()


@router.get(
    "/{dataset_id}",
    response_model=DatasetDetail,
    summary="Get dataset details",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("30/minute")
async def get_dataset(
    request: Request,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a dataset including schema and sample data."""
    service = DatasetService(db)
    result = await service.get_dataset_detail(dataset_id)
    if not result:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return result


@router.delete(
    "/{dataset_id}",
    summary="Delete a dataset",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("10/minute")
async def delete_dataset(
    request: Request,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a dataset and its cached data."""
    service = DatasetService(db)
    deleted = await service.delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": "Dataset deleted successfully", "dataset_id": dataset_id}
