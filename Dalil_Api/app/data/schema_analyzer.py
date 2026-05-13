"""
Schema Analyzer
===============
Automatically detects column types, statistics, and relationships.
Generates a compact schema representation for the LLM.
"""

from typing import Any, Dict, List

import polars as pl

from app.config import get_logger
from app.schemas.datasets import ColumnInfo, DatasetSchema

logger = get_logger(__name__)


class SchemaAnalyzer:
    """Analyzes a DataFrame and produces a structured schema."""

    @staticmethod
    def analyze(df: pl.DataFrame, dataset_id: str, filename: str) -> DatasetSchema:
        """
        Full schema analysis:
        - Column names and types
        - Null counts
        - Unique value counts
        - Basic statistics for numeric columns
        - Sample values for each column
        """
        columns = []

        for col_name in df.columns:
            col = df[col_name]
            dtype_str = str(col.dtype)

            col_info = ColumnInfo(
                name=col_name,
                dtype=dtype_str,
                nullable=col.null_count() > 0,
                unique_count=col.n_unique(),
                sample_values=SchemaAnalyzer._get_sample_values(col),
                stats=SchemaAnalyzer._get_column_stats(col),
            )
            columns.append(col_info)

        schema = DatasetSchema(
            dataset_id=dataset_id,
            filename=filename,
            row_count=df.height,
            column_count=df.width,
            columns=columns,
            file_size_bytes=df.estimated_size(),
        )

        logger.info(
            "schema_analyzed",
            dataset_id=dataset_id,
            rows=df.height,
            cols=df.width,
        )

        return schema

    @staticmethod
    def _get_sample_values(col: pl.Series, n: int = 5) -> List[Any]:
        """Get a few non-null sample values from a column."""
        try:
            non_null = col.drop_nulls()
            if non_null.len() == 0:
                return []
            unique = non_null.unique()
            samples = unique.head(min(n, unique.len())).to_list()
            # Convert to JSON-safe types
            return [str(v) if not isinstance(v, (int, float, str, bool)) else v for v in samples]
        except Exception:
            return []

    @staticmethod
    def _get_column_stats(col: pl.Series) -> Dict[str, Any]:
        """Compute basic statistics for numeric columns."""
        stats = {"null_count": col.null_count()}

        if col.dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                         pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                         pl.Float32, pl.Float64):
            try:
                stats.update({
                    "min": col.min(),
                    "max": col.max(),
                    "mean": round(col.mean(), 2) if col.mean() is not None else None,
                    "median": col.median(),
                    "std": round(col.std(), 2) if col.std() is not None else None,
                })
            except Exception:
                pass

        elif col.dtype == pl.Utf8:
            stats["avg_length"] = round(col.str.len_chars().mean() or 0, 1)

        elif col.dtype in (pl.Date, pl.Datetime):
            try:
                stats["min"] = str(col.min())
                stats["max"] = str(col.max())
            except Exception:
                pass

        return stats

    @staticmethod
    def schema_to_prompt_text(schema: DatasetSchema) -> str:
        """
        Convert schema to a compact text representation for the LLM prompt.
        This is a KEY token-saving technique — we send schema, not raw data.
        """
        lines = [
            f"Dataset: {schema.filename}",
            f"Rows: {schema.row_count:,} | Columns: {schema.column_count}",
            "",
            "Columns:",
        ]

        for col in schema.columns:
            line = f"  - {col.name} ({col.dtype})"
            if col.stats:
                stat_parts = []
                for k, v in col.stats.items():
                    if v is not None and k != "null_count":
                        stat_parts.append(f"{k}={v}")
                if stat_parts:
                    line += f" [{', '.join(stat_parts)}]"
            if col.sample_values:
                samples = ", ".join(str(v) for v in col.sample_values[:3])
                line += f" examples: [{samples}]"
            lines.append(line)

        return "\n".join(lines)
