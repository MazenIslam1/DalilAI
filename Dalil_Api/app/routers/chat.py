"""
Chat Router
===========
Endpoints for chatting with Dalil AI about uploaded datasets.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.middleware.auth import verify_api_key
from app.middleware.rate_limiter import limiter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send a message to Dalil AI",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a question about your uploaded data to Dalil AI.

    **Required fields:**
    - `message`: Your question (e.g., "What are the top 5 products by revenue?")
    - `dataset_id`: The ID returned from file upload

    **Optional fields:**
    - `conversation_id`: Include to continue an existing conversation

    **What Dalil AI can do:**
    - Answer questions about your data
    - Generate insights and trends
    - Detect anomalies
    - Suggest business optimizations
    - Execute data analysis code
    """
    try:
        service = ChatService(db)
        response = await service.process_message(chat_request)
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}",
        )
