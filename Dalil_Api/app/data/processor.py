"""
Data Processor
==============
Handles ingestion of CSV and Excel files using Polars.
Converts to Parquet for fast repeated access.
"""

from pathlib import Path
from typing import Optional, Tuple

import polars as pl

from app.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class DataProcessor:
    """Ingests CSV/Excel files and converts to optimized Parquet format."""

    @staticmethod
    def read_file(filepath: Path) -> pl.DataFrame:
        """
        Read a CSV or Excel file into a Polars DataFrame.
        Handles encoding issues and large files gracefully.
        """
        ext = filepath.suffix.lower()
        logger.info("reading_file", path=str(filepath), extension=ext)

        try:
            if ext == ".csv":
                # Try UTF-8 first, fallback to latin-1
                try:
                    df = pl.read_csv(filepath, infer_schema_length=10000)
                except Exception:
                    df = pl.read_csv(
                        filepath, encoding="latin-1", infer_schema_length=10000
                    )
            elif ext in (".xlsx", ".xls"):
                # Polars reads Excel via calamine/openpyxl
                import pandas as pd

                # Use pandas for Excel (more robust), then convert to Polars
                pdf = pd.read_excel(filepath, engine="openpyxl" if ext == ".xlsx" else "xlrd")
                df = pl.from_pandas(pdf)
            else:
                raise ValueError(f"Unsupported file format: {ext}")

            logger.info(
                "file_read_success",
                rows=df.height,
                columns=df.width,
                columns_list=df.columns,
            )
            return df

        except Exception as e:
            logger.error("file_read_error", error=str(e), path=str(filepath))
            raise

    @staticmethod
    def save_as_parquet(df: pl.DataFrame, dataset_id: str) -> Path:
        """
        Cache the DataFrame as Parquet for fast subsequent reads.
        Parquet is columnar, compressed, and ~10x faster to read than CSV.
        """
        parquet_path = settings.cache_path / f"{dataset_id}.parquet"
        df.write_parquet(parquet_path, compression="zstd")
        logger.info("parquet_saved", path=str(parquet_path), rows=df.height)
        return parquet_path

    @staticmethod
    def load_parquet(dataset_id: str) -> Optional[pl.DataFrame]:
        """Load a cached Parquet file if it exists."""
        parquet_path = settings.cache_path / f"{dataset_id}.parquet"
        if parquet_path.exists():
            return pl.read_parquet(parquet_path)
        return None

    @staticmethod
    def load_parquet_lazy(dataset_id: str) -> Optional[pl.LazyFrame]:
        """
        Load Parquet as a LazyFrame for large datasets.
        LazyFrame defers execution until .collect() — enables query optimization.
        """
        parquet_path = settings.cache_path / f"{dataset_id}.parquet"
        if parquet_path.exists():
            return pl.scan_parquet(parquet_path)
        return None

    @staticmethod
    def get_basic_info(df: pl.DataFrame) -> dict:
        """Get basic DataFrame info without loading full data."""
        return {
            "rows": df.height,
            "columns": df.width,
            "column_names": df.columns,
            "dtypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
            "memory_bytes": df.estimated_size(),
        }

    @staticmethod
    def ingest_file(filepath: Path, dataset_id: str) -> Tuple[pl.DataFrame, Path]:
        """
        Full ingestion pipeline: read → clean → cache as Parquet.
        Returns the DataFrame and the Parquet path.
        """
        df = DataProcessor.read_file(filepath)

        # Basic cleaning
        df = DataProcessor._clean_dataframe(df)

        # Cache as Parquet
        parquet_path = DataProcessor.save_as_parquet(df, dataset_id)

        return df, parquet_path

    @staticmethod
    def _clean_dataframe(df: pl.DataFrame) -> pl.DataFrame:
        """
        Apply basic cleaning:
        - Strip whitespace from string columns
        - Normalize column names (lowercase, underscores)
        """
        # Normalize column names
        rename_map = {}
        for col in df.columns:
            clean_name = col.strip().lower().replace(" ", "_").replace("-", "_")
            # Remove non-alphanumeric except underscores
            clean_name = "".join(c for c in clean_name if c.isalnum() or c == "_")
            if clean_name != col:
                rename_map[col] = clean_name

        if rename_map:
            df = df.rename(rename_map)

        # Strip whitespace from string columns
        string_cols = [
            col for col, dtype in zip(df.columns, df.dtypes) if dtype == pl.Utf8
        ]
        if string_cols:
            df = df.with_columns(
                [pl.col(col).str.strip_chars() for col in string_cols]
            )

        return df

    @staticmethod
    def to_pandas(df: pl.DataFrame):
        """Convert Polars DataFrame to Pandas for code execution context."""
        return df.to_pandas()
