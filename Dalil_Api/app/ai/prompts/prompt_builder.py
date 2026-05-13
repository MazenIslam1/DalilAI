"""
Dynamic Prompt Builder
======================
Constructs optimized prompts by assembling components within token budgets.
This is the central token-saving orchestrator.
"""

from typing import Dict, List, Optional

from app.ai.prompts.analysis_prompts import GENERAL_ANALYSIS_PROMPT
from app.config import get_settings
from app.data.schema_analyzer import SchemaAnalyzer
from app.schemas.datasets import DatasetSchema
from app.utils.token_counter import budget_allocation, estimate_tokens, truncate_to_token_limit

settings = get_settings()


class PromptBuilder:
    """
    Builds prompts that fit within token budgets.
    Dynamically adjusts content based on available space.
    """

    def __init__(self, max_tokens: int = None):
        self.max_tokens = max_tokens or settings.MAX_CONTEXT_TOKENS

    def build_analysis_prompt(
        self,
        question: str,
        schema: DatasetSchema,
        sample_data: str,
        conversation_history: Optional[str] = None,
    ) -> str:
        """
        Build a complete analysis prompt within token budget.

        Token allocation strategy:
        - Schema: ~20% (compact representation)
        - Sample data: ~25% (representative rows)
        - History: ~30% (compressed conversation)
        - Question + buffer: ~25%
        """
        # Convert schema to compact text
        schema_text = SchemaAnalyzer.schema_to_prompt_text(schema)
        schema_tokens = estimate_tokens(schema_text)

        # Calculate budgets
        budgets = budget_allocation(
            total_budget=self.max_tokens,
            system_prompt_tokens=200,  # System prompt is separate in Gemini
            schema_tokens=schema_tokens,
        )

        # Truncate sample data to budget
        sample_text = truncate_to_token_limit(sample_data, budgets["sample_data"])

        # Truncate history to budget
        history_text = ""
        if conversation_history:
            history_text = truncate_to_token_limit(
                f"CONVERSATION CONTEXT:\n{conversation_history}",
                budgets["history"],
            )

        # Assemble the prompt
        column_names = ", ".join(schema.columns[i].name for i in range(len(schema.columns)))

        prompt = GENERAL_ANALYSIS_PROMPT.format(
            schema=schema_text,
            sample=sample_text,
            conversation_context=history_text,
            question=question,
            column_names=column_names,
        )

        return prompt

    def build_insight_prompt(
        self,
        schema: DatasetSchema,
        sample_data: str,
        insight_type: str = "general",
    ) -> str:
        """Build a prompt specifically for insight generation."""
        from app.ai.prompts.analysis_prompts import (
            ANOMALY_DETECTION_PROMPT,
            INSIGHT_GENERATION_PROMPT,
            OPTIMIZATION_PROMPT,
            TREND_DETECTION_PROMPT,
        )

        schema_text = SchemaAnalyzer.schema_to_prompt_text(schema)
        sample_text = truncate_to_token_limit(sample_data, self.max_tokens // 3)

        template_map = {
            "trend": TREND_DETECTION_PROMPT,
            "anomaly": ANOMALY_DETECTION_PROMPT,
            "optimization": OPTIMIZATION_PROMPT,
            "general": INSIGHT_GENERATION_PROMPT,
        }

        template = template_map.get(insight_type, INSIGHT_GENERATION_PROMPT)

        return template.format(schema=schema_text, sample=sample_text)

    @staticmethod
    def detect_query_intent(query: str) -> str:
        """
        Simple keyword-based intent detection.
        Determines what type of analysis prompt to use.
        """
        query_lower = query.lower()

        trend_keywords = ["trend", "growth", "increase", "decrease", "over time", "pattern",
                          "اتجاه", "نمو", "زيادة", "نقصان"]
        anomaly_keywords = ["anomaly", "outlier", "unusual", "abnormal", "spike",
                            "شذوذ", "غريب", "غير طبيعي"]
        optimization_keywords = ["optimize", "improve", "recommend", "suggestion", "better",
                                 "تحسين", "توصية", "اقتراح"]

        if any(kw in query_lower for kw in trend_keywords):
            return "trend"
        if any(kw in query_lower for kw in anomaly_keywords):
            return "anomaly"
        if any(kw in query_lower for kw in optimization_keywords):
            return "optimization"
        return "general"
