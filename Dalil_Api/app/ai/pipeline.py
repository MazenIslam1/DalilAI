"""
AI Processing Pipeline
======================
The main orchestrator that ties together all AI components.
Handles the full flow: context building → Gemini call → code execution → response formatting.
"""

from typing import Optional

import polars as pl
from fastapi.concurrency import run_in_threadpool

from app.ai.code_executor import execute_code_safely, extract_code_blocks
from app.ai.context.context_manager import context_manager
from app.ai.context.memory import conversation_memory
from app.ai.gemini_client import GeminiClient, get_gemini_client
from app.ai.prompts.prompt_builder import PromptBuilder
from app.config import get_logger
from app.data.cache import response_cache
from app.data.processor import DataProcessor
from app.schemas.chat import ChatResponse, DataInsight
from app.schemas.datasets import DatasetSchema
from app.utils.helpers import generate_id
from app.utils.token_counter import estimate_tokens

logger = get_logger(__name__)


class AIPipeline:
    """
    6-stage AI processing pipeline:

    1. Cache Check  → Return cached response if identical query exists
    2. Context Build → Schema + sample + history within token budget
    3. Gemini Call   → Send optimized prompt to Gemini 2.5 Flash
    4. Code Extract  → Parse Python code blocks from response
    5. Code Execute  → Run code in sandbox against the actual data
    6. Response Format → Combine AI text + execution results
    """

    def __init__(self):
        self.gemini: GeminiClient = get_gemini_client()
        self.prompt_builder = PromptBuilder()

    async def process_query(
        self,
        question: str,
        dataset_id: str,
        schema: DatasetSchema,
        df: pl.DataFrame,
        conversation_id: str,
    ) -> ChatResponse:
        """
        Main entry point — process a user question through the full pipeline.
        """
        logger.info(
            "pipeline_start",
            dataset_id=dataset_id,
            conversation_id=conversation_id,
            question_length=len(question),
        )

        # ── Stage 1: Cache Check ────────────────────────────────
        cached = response_cache.get(question, dataset_id)
        if cached:
            logger.info("pipeline_cache_hit", dataset_id=dataset_id)
            return ChatResponse(
                conversation_id=conversation_id,
                message=self._strip_code_blocks(cached),
                tokens_used=0,
            )

        # ── Stage 2: Build Context ──────────────────────────────
        prompt = context_manager.build_context(
            question=question,
            schema=schema,
            df=df,
            conversation_id=conversation_id,
        )

        prompt_tokens = estimate_tokens(prompt)
        logger.info("pipeline_context_built", prompt_tokens=prompt_tokens)

        # ── Stage 3: Call Gemini ────────────────────────────────
        is_first_message = conversation_memory.get_message_count(conversation_id) == 0

        if is_first_message:
            ai_response = await self.gemini.generate_with_full_system(prompt)
        else:
            ai_response = await self.gemini.generate(prompt)

        response_tokens = estimate_tokens(ai_response)
        total_tokens = prompt_tokens + response_tokens

        # ── Stage 4: Extract Code ───────────────────────────────
        code_blocks = extract_code_blocks(ai_response)

        # ── Stage 5: Execute Code ───────────────────────────────
        execution_result = None
        executed_code = None
        insights = []

        if code_blocks:
            # Convert Polars to Pandas for code execution (LLM generates pandas code)
            pandas_df = await run_in_threadpool(DataProcessor.to_pandas, df)

            for code in code_blocks:
                executed_code = code
                execution_result = await run_in_threadpool(
                    execute_code_safely, code, pandas_df
                )

                if execution_result["success"]:
                    break  # Use first successful code block
                else:
                    logger.warning(
                        "code_execution_failed",
                        error=execution_result.get("error"),
                    )

        # ── Stage 6: Format Response ────────────────────────────
        # Strip code blocks from the AI message — keep only natural language
        clean_message = self._strip_code_blocks(ai_response)

        # Store in memory
        conversation_memory.add_message(conversation_id, "user", question)
        conversation_memory.add_message(conversation_id, "assistant", clean_message)

        # Cache the response
        response_cache.put(question, dataset_id, ai_response)

        # Trigger summarization if needed (non-blocking)
        await context_manager.maybe_summarize(conversation_id, self.gemini)

        response = ChatResponse(
            conversation_id=conversation_id,
            message=clean_message,
            code_executed=executed_code,
            execution_result=execution_result if execution_result else None,
            tokens_used=total_tokens,
        )

        logger.info(
            "pipeline_complete",
            total_tokens=total_tokens,
            had_code=bool(code_blocks),
            code_success=execution_result["success"] if execution_result else None,
        )

        return response

    @staticmethod
    def _strip_code_blocks(text: str) -> str:
        """Remove ```python ... ``` code blocks from the AI message, keeping only natural language."""
        import re
        # Remove fenced code blocks
        cleaned = re.sub(r"```[\w]*\n.*?```", "", text, flags=re.DOTALL)
        # Collapse extra blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()


# Singleton
_pipeline: Optional[AIPipeline] = None


def get_pipeline() -> AIPipeline:
    """Get or create the singleton pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = AIPipeline()
    return _pipeline
