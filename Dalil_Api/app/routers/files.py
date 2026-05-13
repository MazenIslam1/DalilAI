"""
File Upload Router
==================
Endpoints for uploading CSV/Excel files.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.middleware.auth import verify_api_key
from app.middleware.rate_limiter import limiter
from app.schemas.files import FileUploadResponse, FileValidationError
from app.services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    responses={
        400: {"model": FileValidationError, "description": "Invalid file"},
        413: {"description": "File too large"},
    },
    summary="Upload a CSV or Excel file for analysis",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="CSV or Excel file to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV or Excel file for Dalil AI analysis.

    The file will be:
    1. Validated (extension, size, security)
    2. Processed and cleaned
    3. Schema auto-detected
    4. Cached as Parquet for fast access

    Returns the dataset_id needed for chat queries.
    """
    try:
        service = FileService(db)
        result = await service.upload_and_process(file)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")
