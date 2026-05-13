"""
Gemini Client
=============
Async wrapper around the Google Gemini 2.5 Flash API.
Handles rate limiting, retries, and error handling.
"""

import asyncio
from typing import Optional

from google import genai
from google.genai.types import GenerateContentConfig

from app.ai.prompts.system_prompts import DALIL_SYSTEM_PROMPT, DALIL_SYSTEM_PROMPT_MINIMAL
from app.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class GeminiClient:
    """
    Async Gemini 2.5 Flash client with built-in retry logic.

    Rate limit handling for free tier:
    - 5 RPM max → queued requests with backoff
    - 429 errors → exponential backoff with jitter
    """

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not set! "
                "Please add it to your .env file. "
                "Get your key from: https://aistudio.google.com/"
            )

        self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self._model = settings.GEMINI_MODEL
        self._max_retries = 3
        self._semaphore = asyncio.Semaphore(2)  # Max 2 concurrent requests

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: int = 4096,
    ) -> str:
        """
        Generate a response from Gemini 2.5 Flash.
        Includes automatic retry with exponential backoff for rate limits.
        """
        if system_prompt is None:
            system_prompt = DALIL_SYSTEM_PROMPT_MINIMAL

        config = GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature or settings.GEMINI_TEMPERATURE,
            max_output_tokens=max_output_tokens,
        )

        async with self._semaphore:
            return await self._call_with_retry(prompt, config)

    async def _call_with_retry(
        self,
        prompt: str,
        config: GenerateContentConfig,
    ) -> str:
        """Call Gemini with exponential backoff on rate limit errors."""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=config,
                )

                if response.text:
                    logger.info(
                        "gemini_response",
                        model=self._model,
                        attempt=attempt + 1,
                        response_length=len(response.text),
                    )
                    return response.text

                logger.warning("gemini_empty_response", attempt=attempt + 1)
                return "I couldn't generate an analysis for this query. Please try rephrasing."

            except Exception as e:
                last_error = e
                error_str = str(e)

                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # Rate limited — back off
                    wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                    logger.warning(
                        "gemini_rate_limited",
                        attempt=attempt + 1,
                        wait_seconds=wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        "gemini_error",
                        error=error_str,
                        attempt=attempt + 1,
                    )
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(1)
                    else:
                        raise

        raise last_error

    async def generate_with_full_system(self, prompt: str) -> str:
        """Generate using the full system prompt (for first message in conversation)."""
        return await self.generate(prompt, system_prompt=DALIL_SYSTEM_PROMPT)


# Singleton
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the singleton Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
