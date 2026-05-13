"""
Data Access Repositories
========================
Async CRUD operations for database models.
"""

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Dataset, Message, generate_uuid


class DatasetRepository:
    """CRUD operations for datasets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Dataset:
        dataset = Dataset(**kwargs)
        self.db.add(dataset)
        await self.db.flush()
        return dataset

    async def get(self, dataset_id: str) -> Optional[Dataset]:
        result = await self.db.execute(select(Dataset).where(Dataset.id == dataset_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Dataset]:
        result = await self.db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
        return list(result.scalars().all())

    async def delete(self, dataset_id: str) -> bool:
        dataset = await self.get(dataset_id)
        if dataset:
            await self.db.delete(dataset)
            return True
        return False

    async def update_schema(self, dataset_id: str, schema_json: str) -> None:
        dataset = await self.get(dataset_id)
        if dataset:
            dataset.schema_json = schema_json
            await self.db.flush()


class ConversationRepository:
    """CRUD operations for conversations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, dataset_id: str) -> Conversation:
        convo = Conversation(id=generate_uuid(), dataset_id=dataset_id)
        self.db.add(convo)
        await self.db.flush()
        return convo

    async def get(self, conversation_id: str) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def update_summary(self, conversation_id: str, summary: str) -> None:
        convo = await self.get(conversation_id)
        if convo:
            convo.summary = summary
            await self.db.flush()

    async def increment_count(self, conversation_id: str) -> None:
        convo = await self.get(conversation_id)
        if convo:
            convo.message_count += 1
            await self.db.flush()


class MessageRepository:
    """CRUD operations for messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, conversation_id: str, role: str, content: str, tokens_used: int = None
    ) -> Message:
        msg = Message(
            id=generate_uuid(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def get_history(
        self, conversation_id: str, limit: int = 20
    ) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # Oldest first
        return messages
