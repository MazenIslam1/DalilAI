"""
Conversation Summarizer
=======================
Compresses long conversation histories into concise summaries.
Uses Gemini to generate summaries, saving tokens in future turns.
"""

from typing import List, Dict

from app.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()

SUMMARIZE_PROMPT = """Summarize this conversation between a user and Dalil AI data analyst.
Keep only the key questions asked, data findings, and conclusions.
Be very concise (max 200 words).

Conversation:
{conversation}

Summary:"""


class ConversationSummarizer:
    """
    Summarizes conversation history to compress tokens.
    Called automatically when conversation exceeds threshold.
    """

    @staticmethod
    def should_summarize(message_count: int) -> bool:
        """Check if the conversation is long enough to warrant summarization."""
        return message_count >= settings.CONVERSATION_SUMMARY_THRESHOLD

    @staticmethod
    def build_summary_prompt(messages: List[Dict[str, str]]) -> str:
        """Build a prompt to summarize conversation history."""
        conversation_text = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Dalil AI"
            # Truncate individual messages for the summary prompt
            content = msg["content"][:300]
            conversation_text += f"{role}: {content}\n\n"

        return SUMMARIZE_PROMPT.format(conversation=conversation_text)

    @staticmethod
    def extract_summary_from_response(response_text: str) -> str:
        """Clean up the summary response."""
        summary = response_text.strip()
        # Limit summary length
        if len(summary) > 1000:
            summary = summary[:1000] + "..."
        return summary
