"""
Tests for AI Pipeline Components
"""

import pandas as pd
import pytest

from app.ai.code_executor import execute_code_safely, extract_code_blocks, validate_code
from app.ai.prompts.prompt_builder import PromptBuilder
from app.ai.context.memory import ConversationMemory
from app.utils.token_counter import estimate_tokens, budget_allocation


class TestCodeExecutor:
    """Tests for sandboxed code execution."""

    def test_execute_safe_code(self, sample_pandas_df):
        """Test executing safe pandas code."""
        code = "result = df['sales'].sum()"
        result = execute_code_safely(code, sample_pandas_df)
        assert result["success"] is True

    def test_block_dangerous_code(self, sample_pandas_df):
        """Test that dangerous code is blocked."""
        code = "import os; os.system('rm -rf /')"
        result = execute_code_safely(code, sample_pandas_df)
        assert result["success"] is False
        assert "Blocked" in result["error"]

    def test_block_file_access(self, sample_pandas_df):
        """Test that file access is blocked."""
        code = "open('/etc/passwd', 'r')"
        result = execute_code_safely(code, sample_pandas_df)
        assert result["success"] is False

    def test_extract_code_blocks(self):
        """Test extracting Python code from markdown."""
        text = """Here's the analysis:
```python
result = df.describe()
```
That's all."""
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert "df.describe()" in blocks[0]

    def test_validate_safe_code(self):
        """Test code validation."""
        safe, error = validate_code("result = df['sales'].mean()")
        assert safe is True
        assert error is None

    def test_validate_dangerous_code(self):
        """Test that dangerous patterns are caught."""
        safe, error = validate_code("import subprocess; subprocess.run(['ls'])")
        assert safe is False


class TestPromptBuilder:
    """Tests for the prompt builder."""

    def test_detect_query_intent(self):
        """Test intent detection."""
        assert PromptBuilder.detect_query_intent("What's the sales trend?") == "trend"
        assert PromptBuilder.detect_query_intent("Find anomalies in the data") == "anomaly"
        assert PromptBuilder.detect_query_intent("How can I optimize revenue?") == "optimization"
        assert PromptBuilder.detect_query_intent("How many products do I have?") == "general"


class TestConversationMemory:
    """Tests for conversation memory."""

    def test_add_and_retrieve(self):
        """Test adding and retrieving messages."""
        memory = ConversationMemory()
        memory.add_message("conv1", "user", "Hello")
        memory.add_message("conv1", "assistant", "Hi there!")

        history = memory.get_history("conv1")
        assert len(history) == 2
        assert history[0]["role"] == "user"

    def test_history_text(self):
        """Test getting history as formatted text."""
        memory = ConversationMemory()
        memory.add_message("conv1", "user", "What are top products?")
        memory.add_message("conv1", "assistant", "Widget A is the top product.")

        text = memory.get_history_text("conv1")
        assert "User:" in text
        assert "Assistant:" in text

    def test_clear(self):
        """Test clearing conversation memory."""
        memory = ConversationMemory()
        memory.add_message("conv1", "user", "Hello")
        memory.clear("conv1")
        assert memory.get_message_count("conv1") == 0


class TestTokenCounter:
    """Tests for token utilities."""

    def test_estimate_tokens(self):
        """Test token estimation."""
        tokens = estimate_tokens("Hello, world!")
        assert tokens > 0
        assert tokens < 100

    def test_budget_allocation(self):
        """Test token budget allocation."""
        budget = budget_allocation(
            total_budget=8000,
            system_prompt_tokens=200,
            schema_tokens=500,
        )
        assert budget["system_prompt"] == 200
        assert budget["schema"] == 500
        assert budget["history"] > 0
        assert budget["sample_data"] > 0
