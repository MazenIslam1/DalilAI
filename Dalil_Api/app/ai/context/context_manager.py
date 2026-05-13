"""
Context Manager
===============
Orchestrates what context gets sent to the LLM within token budgets.
This is the KEY module for token optimization.
"""

from typing import Dict, List, Optional

import polars as pl

from app.ai.context.memory import conversation_memory
from app.ai.context.summarizer import ConversationSummarizer
from app.ai.prompts.prompt_builder import PromptBuilder
from app.config import get_logger, get_settings
from app.data.sampler import DataSampler
from app.data.schema_analyzer import SchemaAnalyzer
from app.schemas.datasets import DatasetSchema
from app.utils.token_counter import estimate_tokens

logger = get_logger(__name__)
settings = get_settings()


class ContextManager:
    """
    Manages what context is injected into each LLM call.

    Token-saving strategies implemented:
    1. Schema-only context (never send raw data)
    2. Smart sampling (representative rows only)
    3. Query-focused column selection
    4. Conversation summarization after N turns
    5. Dynamic budget allocation
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.summarizer = ConversationSummarizer()

    def build_context(
        self,
        question: str,
        schema: DatasetSchema,
        df: pl.DataFrame,
        conversation_id: str,
    ) -> str:
        """
        Build the complete context for a Gemini call.
        Returns an optimized prompt string.
        """
        # 1. Get query-focused data sample (only relevant columns/rows)
        sample_text = DataSampler.get_query_focused_sample(df, question)

        # 2. Get compressed conversation history
        history_text = conversation_memory.get_history_text(conversation_id)

        # 3. Build prompt within token budget
        prompt = self.prompt_builder.build_analysis_prompt(
            question=question,
            schema=schema,
            sample_data=sample_text,
            conversation_history=history_text if history_text else None,
        )

        logger.info(
            "context_built",
            estimated_tokens=estimate_tokens(prompt),
            has_history=bool(history_text),
        )

        return prompt

    async def maybe_summarize(
        self,
        conversation_id: str,
        gemini_client,
    ) -> None:
        """
        Summarize conversation if it's getting long.
        This compresses old messages into a summary to save tokens.
        """
        msg_count = conversation_memory.get_message_count(conversation_id)

        if not self.summarizer.should_summarize(msg_count):
            return

        # Get older messages to summarize (keep last 4 turns un-summarized)
        all_messages = conversation_memory.get_history(conversation_id, last_n=50)
        messages_to_summarize = all_messages[:-8]  # Keep last 8 messages (4 turns)

        if not messages_to_summarize:
            return

        # Build summary prompt
        summary_prompt = self.summarizer.build_summary_prompt(messages_to_summarize)

        try:
            # Call Gemini for summarization
            summary_response = await gemini_client.generate(summary_prompt)
            summary = self.summarizer.extract_summary_from_response(summary_response)

            # Store the summary
            conversation_memory.set_summary(conversation_id, summary)

            logger.info(
                "conversation_summarized",
                conversation_id=conversation_id,
                original_messages=len(messages_to_summarize),
                summary_tokens=estimate_tokens(summary),
            )
        except Exception as e:
            logger.error("summarization_failed", error=str(e))
            # Non-critical — just continue without summarization


# Singleton
context_manager = ContextManager()
