"""
Data Analysis Tools
===================
Predefined analysis functions that the AI can invoke.
These provide accurate computations without relying on LLM arithmetic.
"""

from typing import Any, Dict, List, Optional

import polars as pl

from app.config import get_logger

logger = get_logger(__name__)


class DataTools:
    """Pre-built data analysis operations."""

    @staticmethod
    def basic_statistics(df: pl.DataFrame) -> Dict[str, Any]:
        """Compute comprehensive statistics for all numeric columns."""
        stats = {}
        for col in df.columns:
            if df[col].dtype in (pl.Int32, pl.Int64, pl.Float32, pl.Float64):
                series = df[col].drop_nulls()
                stats[col] = {
                    "count": series.len(),
                    "mean": round(series.mean(), 2),
                    "median": series.median(),
                    "std": round(series.std(), 2),
                    "min": series.min(),
                    "max": series.max(),
                    "q25": series.quantile(0.25),
                    "q75": series.quantile(0.75),
                }
        return stats

    @staticmethod
    def value_counts(df: pl.DataFrame, column: str, top_n: int = 10) -> Dict[str, int]:
        """Get top value counts for a column."""
        if column not in df.columns:
            return {}
        counts = df[column].value_counts().sort("count", descending=True).head(top_n)
        return dict(zip(counts[column].to_list(), counts["count"].to_list()))

    @staticmethod
    def correlation_matrix(df: pl.DataFrame) -> Optional[Dict]:
        """Compute correlation matrix for numeric columns."""
        numeric_cols = [
            col for col in df.columns
            if df[col].dtype in (pl.Int32, pl.Int64, pl.Float32, pl.Float64)
        ]
        if len(numeric_cols) < 2:
            return None

        # Convert to pandas for correlation
        pdf = df.select(numeric_cols).to_pandas()
        corr = pdf.corr()
        return corr.to_dict()

    @staticmethod
    def group_summary(
        df: pl.DataFrame,
        group_col: str,
        value_col: str,
        agg: str = "sum",
    ) -> Dict[str, Any]:
        """Group by a column and aggregate another."""
        if group_col not in df.columns or value_col not in df.columns:
            return {}

        agg_map = {
            "sum": pl.col(value_col).sum(),
            "mean": pl.col(value_col).mean(),
            "count": pl.col(value_col).count(),
            "min": pl.col(value_col).min(),
            "max": pl.col(value_col).max(),
        }

        agg_expr = agg_map.get(agg, pl.col(value_col).sum())
        result = df.group_by(group_col).agg(agg_expr).sort(value_col, descending=True)

        return {
            str(row[0]): row[1]
            for row in result.iter_rows()
        }

    @staticmethod
    def detect_missing_data(df: pl.DataFrame) -> Dict[str, Dict]:
        """Analyze missing data patterns."""
        missing = {}
        for col in df.columns:
            null_count = df[col].null_count()
            if null_count > 0:
                missing[col] = {
                    "null_count": null_count,
                    "null_percentage": round(null_count / df.height * 100, 2),
                }
        return missing
