"""
Token Counting Utilities
========================
Estimates token count for prompts to stay within budget.
Gemini uses a tokenizer similar to SentencePiece — we approximate at ~4 chars/token.
"""

from typing import List, Dict, Any

# Average characters per token for Gemini models (conservative estimate)
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


def estimate_tokens_for_messages(messages: List[Dict[str, str]]) -> int:
    """Estimate total tokens for a list of messages."""
    total = 0
    for msg in messages:
        total += estimate_tokens(msg.get("role", ""))
        total += estimate_tokens(msg.get("content", ""))
        total += 4  # Overhead per message (role markers, separators)
    return total


def estimate_tokens_for_schema(schema_text: str) -> int:
    """Estimate tokens for schema representation."""
    return estimate_tokens(schema_text)


def truncate_to_token_limit(text: str, max_tokens: int) -> str:
    """Truncate text to fit within a token budget."""
    max_chars = max_tokens * CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def budget_allocation(
    total_budget: int,
    system_prompt_tokens: int,
    schema_tokens: int,
) -> Dict[str, int]:
    """
    Allocate token budget across prompt components.
    Returns how many tokens each component can use.
    """
    remaining = total_budget - system_prompt_tokens - schema_tokens
    if remaining < 500:
        remaining = 500  # Minimum for conversation

    return {
        "system_prompt": system_prompt_tokens,
        "schema": schema_tokens,
        "history": int(remaining * 0.4),   # 40% for conversation history
        "sample_data": int(remaining * 0.3),  # 30% for data samples
        "user_query": int(remaining * 0.3),   # 30% for current query + buffer
    }
