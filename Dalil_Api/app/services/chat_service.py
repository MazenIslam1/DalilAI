"""
Chat Service
=============
Orchestrates the chat flow: loads data, runs AI pipeline, stores messages.
"""

import json
from typing import Optional

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.pipeline import get_pipeline
from app.config import get_logger
from app.data.processor import DataProcessor
from app.data.schema_analyzer import SchemaAnalyzer
from app.db.repositories import ConversationRepository, DatasetRepository, MessageRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.datasets import DatasetSchema

logger = get_logger(__name__)


class ChatService:
    """Orchestrates the full chat interaction flow."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dataset_repo = DatasetRepository(db)
        self.convo_repo = ConversationRepository(db)
        self.msg_repo = MessageRepository(db)

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process an incoming chat message:
        1. Load or create conversation
        2. Load dataset (from Parquet cache)
        3. Load schema metadata
        4. Run AI pipeline
        5. Store messages in DB
        """
        # ── Load Dataset ────────────────────────────────────────
        dataset = await self.dataset_repo.get(request.dataset_id)
        if not dataset:
            raise ValueError(f"Dataset '{request.dataset_id}' not found")

        # Load data from Parquet cache (fast)
        df = await run_in_threadpool(DataProcessor.load_parquet, request.dataset_id)
        if df is None:
            raise ValueError(f"Dataset data not found. Please re-upload the file.")

        # Load schema
        schema = self._parse_schema(dataset.schema_json, dataset)

        # ── Load/Create Conversation ────────────────────────────
        conversation_id = request.conversation_id
        if conversation_id:
            convo = await self.convo_repo.get(conversation_id)
            if not convo:
                raise ValueError(f"Conversation '{conversation_id}' not found")
        else:
            convo = await self.convo_repo.create(dataset_id=request.dataset_id)
            conversation_id = convo.id

        # ── Run AI Pipeline ─────────────────────────────────────
        pipeline = get_pipeline()
        response = await pipeline.process_query(
            question=request.message,
            dataset_id=request.dataset_id,
            schema=schema,
            df=df,
            conversation_id=conversation_id,
        )

        # ── Store Messages in DB ────────────────────────────────
        await self.msg_repo.create(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )
        await self.msg_repo.create(
            conversation_id=conversation_id,
            role="assistant",
            content=response.message,
            tokens_used=response.tokens_used,
        )
        await self.convo_repo.increment_count(conversation_id)

        logger.info(
            "chat_processed",
            conversation_id=conversation_id,
            tokens_used=response.tokens_used,
        )

        return response

    def _parse_schema(self, schema_json: str, dataset) -> DatasetSchema:
        """Parse stored schema JSON back into a DatasetSchema object."""
        if schema_json:
            try:
                schema_data = json.loads(schema_json)
                return DatasetSchema(**schema_data)
            except Exception:
                pass

        # Fallback: create minimal schema
        return DatasetSchema(
            dataset_id=dataset.id,
            filename=dataset.filename,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            columns=[],
            file_size_bytes=dataset.file_size_bytes,
        )
