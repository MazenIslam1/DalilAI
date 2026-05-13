"""
Smart Data Sampler
==================
Extracts representative samples from data for LLM context injection.
Uses intelligent sampling to maximize information while minimizing tokens.
"""

from typing import Dict, List, Optional

import polars as pl

from app.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class DataSampler:
    """
    Generates minimal but representative data samples for LLM prompts.
    This is critical for token optimization — we never send full datasets.
    """

    @staticmethod
    def get_representative_sample(
        df: pl.DataFrame,
        n_rows: int = None,
        relevant_columns: Optional[List[str]] = None,
    ) -> str:
        """
        Get a representative sample as formatted text.

        Strategy:
        1. Select only relevant columns (if specified by query analysis)
        2. Take head rows + a few random rows for diversity
        3. Format as a compact table
        """
        n_rows = n_rows or settings.MAX_SAMPLE_ROWS

        # Column selection optimization
        if relevant_columns:
            valid_cols = [c for c in relevant_columns if c in df.columns]
            if valid_cols:
                df = df.select(valid_cols)

        sample = DataSampler._smart_sample(df, n_rows)
        return DataSampler._format_as_text(sample)

    @staticmethod
    def _smart_sample(df: pl.DataFrame, n_rows: int) -> pl.DataFrame:
        """
        Intelligent sampling strategy:
        - First 3 rows (show structure)
        - Last 2 rows (show range)
        - Random rows from middle (show diversity)
        """
        if df.height <= n_rows:
            return df

        head_n = min(3, n_rows // 3)
        tail_n = min(2, n_rows // 4)
        random_n = n_rows - head_n - tail_n

        parts = [df.head(head_n)]

        if random_n > 0 and df.height > head_n + tail_n:
            middle = df.slice(head_n, df.height - head_n - tail_n)
            if middle.height > 0:
                parts.append(middle.sample(min(random_n, middle.height), seed=42))

        if tail_n > 0:
            parts.append(df.tail(tail_n))

        return pl.concat(parts)

    @staticmethod
    def get_query_focused_sample(
        df: pl.DataFrame,
        query: str,
        n_rows: int = None,
    ) -> str:
        """
        Extract a sample focused on what the query is asking about.
        Uses keyword matching to filter relevant rows before sampling.
        """
        n_rows = n_rows or settings.MAX_SAMPLE_ROWS

        # Try to find columns mentioned in the query
        query_lower = query.lower()
        relevant_cols = [
            col for col in df.columns if col.lower() in query_lower
        ]

        # Try to find filter values in the query for string columns
        filtered_df = df
        for col in df.columns:
            if df[col].dtype == pl.Utf8:
                try:
                    unique_vals = df[col].drop_nulls().unique().to_list()
                    for val in unique_vals[:50]:  # Check first 50 unique values
                        if str(val).lower() in query_lower:
                            filtered_df = df.filter(pl.col(col) == val)
                            break
                except Exception:
                    continue

        if filtered_df.height > 0 and filtered_df.height < df.height:
            # We found relevant rows
            sample_df = filtered_df
        else:
            sample_df = df

        return DataSampler.get_representative_sample(
            sample_df, n_rows, relevant_cols if relevant_cols else None
        )

    @staticmethod
    def _format_as_text(df: pl.DataFrame) -> str:
        """Format a small DataFrame as a compact text table."""
        if df.height == 0:
            return "(empty dataset)"

        # Use pipe-separated format for compactness
        headers = " | ".join(df.columns)
        separator = "-" * len(headers)
        rows = []
        for row in df.iter_rows():
            row_str = " | ".join(
                str(v) if v is not None else "NULL" for v in row
            )
            rows.append(row_str)

        return f"{headers}\n{separator}\n" + "\n".join(rows)

    @staticmethod
    def get_column_summary(df: pl.DataFrame) -> Dict:
        """
        Quick summary of all columns — useful for query routing.
        Much cheaper than sending raw data.
        """
        summary = {}
        for col in df.columns:
            series = df[col]
            info = {
                "dtype": str(series.dtype),
                "non_null": series.len() - series.null_count(),
                "unique": series.n_unique(),
            }
            summary[col] = info
        return summary
