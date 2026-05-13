"""
Chat Request/Response Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from the user."""

    message: str = Field(..., min_length=1, max_length=5000, description="User's question")
    dataset_id: str = Field(..., description="ID of the dataset to analyze")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")


class DataInsight(BaseModel):
    """A single insight extracted from data analysis."""

    type: str = Field(..., description="Type: trend, anomaly, optimization, summary")
    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    data: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response sent back to the user."""

    conversation_id: str
    message: str = Field(..., description="AI response text")
    insights: List[DataInsight] = Field(default_factory=list)
    code_executed: Optional[str] = Field(None, description="Code that was run (if any)")
    execution_result: Optional[Dict[str, Any]] = Field(None, description="Raw execution result")
    tokens_used: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """A conversation turn for memory."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
