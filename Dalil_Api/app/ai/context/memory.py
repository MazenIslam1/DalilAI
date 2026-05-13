"""
Conversation Memory
===================
Manages conversation history with compression for token optimization.
"""

from typing import Dict, List, Optional

from app.config import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """
    In-memory conversation buffer with automatic compression.
    Keeps recent messages in full, compresses older ones into summaries.
    """

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self._conversations: Dict[str, List[Dict[str, str]]] = {}
        self._summaries: Dict[str, str] = {}

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to the conversation."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []

        self._conversations[conversation_id].append({
            "role": role,
            "content": content,
        })

        # Trim if too long (keep last N turns)
        if len(self._conversations[conversation_id]) > self.max_turns * 2:
            self._conversations[conversation_id] = self._conversations[conversation_id][
                -self.max_turns * 2 :
            ]

    def get_history(self, conversation_id: str, last_n: int = 6) -> List[Dict[str, str]]:
        """Get the last N messages for a conversation."""
        messages = self._conversations.get(conversation_id, [])
        return messages[-last_n * 2 :] if messages else []

    def get_history_text(self, conversation_id: str, last_n: int = 4) -> str:
        """
        Get conversation history as formatted text for prompt injection.
        Combines the compressed summary with recent messages.
        """
        parts = []

        # Include summary of older conversation if exists
        summary = self._summaries.get(conversation_id)
        if summary:
            parts.append(f"Previous conversation summary: {summary}")

        # Include recent messages
        recent = self.get_history(conversation_id, last_n)
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            # Truncate very long messages
            content = msg["content"][:500]
            parts.append(f"{role}: {content}")

        return "\n".join(parts) if parts else ""

    def set_summary(self, conversation_id: str, summary: str) -> None:
        """Store a compressed summary of older conversation turns."""
        self._summaries[conversation_id] = summary
        logger.info("conversation_summary_set", conversation_id=conversation_id)

    def get_message_count(self, conversation_id: str) -> int:
        """Get total messages in a conversation."""
        return len(self._conversations.get(conversation_id, []))

    def clear(self, conversation_id: str) -> None:
        """Clear a conversation's memory."""
        self._conversations.pop(conversation_id, None)
        self._summaries.pop(conversation_id, None)


# Singleton instance
conversation_memory = ConversationMemory()
