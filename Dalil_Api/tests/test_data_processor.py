"""
Tests for Data Processing Layer
"""

import polars as pl
import pytest

from app.data.processor import DataProcessor
from app.data.schema_analyzer import SchemaAnalyzer
from app.data.sampler import DataSampler
from app.data.cache import ResponseCache


class TestDataProcessor:
    """Tests for the DataProcessor."""

    def test_read_csv(self, sample_csv_path):
        """Test reading a CSV file."""
        df = DataProcessor.read_file(sample_csv_path)
        assert isinstance(df, pl.DataFrame)
        assert df.height == 5
        assert df.width == 5
        assert "product" in df.columns

    def test_clean_dataframe(self, sample_polars_df):
        """Test DataFrame cleaning."""
        # Create a df with messy column names
        messy_df = sample_polars_df.rename({
            "product": "Product Name",
            "sales": "Total Sales",
        })
        cleaned = DataProcessor._clean_dataframe(messy_df)
        assert "product_name" in cleaned.columns
        assert "total_sales" in cleaned.columns

    def test_get_basic_info(self, sample_polars_df):
        """Test basic info extraction."""
        info = DataProcessor.get_basic_info(sample_polars_df)
        assert info["rows"] == 5
        assert info["columns"] == 4
        assert "product" in info["column_names"]


class TestSchemaAnalyzer:
    """Tests for SchemaAnalyzer."""

    def test_analyze(self, sample_polars_df):
        """Test schema analysis."""
        schema = SchemaAnalyzer.analyze(sample_polars_df, "test_id", "test.csv")
        assert schema.dataset_id == "test_id"
        assert schema.row_count == 5
        assert schema.column_count == 4
        assert len(schema.columns) == 4

    def test_schema_to_prompt_text(self, sample_polars_df):
        """Test schema to prompt text conversion."""
        schema = SchemaAnalyzer.analyze(sample_polars_df, "test_id", "test.csv")
        text = SchemaAnalyzer.schema_to_prompt_text(schema)
        assert "test.csv" in text
        assert "product" in text
        assert "sales" in text

    def test_column_stats(self, sample_polars_df):
        """Test column statistics."""
        stats = SchemaAnalyzer._get_column_stats(sample_polars_df["sales"])
        assert "min" in stats
        assert "max" in stats
        assert stats["min"] == 100
        assert stats["max"] == 300


class TestDataSampler:
    """Tests for DataSampler."""

    def test_representative_sample(self, sample_polars_df):
        """Test representative sampling."""
        sample = DataSampler.get_representative_sample(sample_polars_df, n_rows=3)
        assert isinstance(sample, str)
        assert "product" in sample

    def test_column_selection(self, sample_polars_df):
        """Test that column selection works."""
        sample = DataSampler.get_representative_sample(
            sample_polars_df, n_rows=3, relevant_columns=["product", "sales"]
        )
        assert "product" in sample
        assert "sales" in sample


class TestResponseCache:
    """Tests for ResponseCache."""

    def test_put_and_get(self):
        """Test basic cache put and get."""
        cache = ResponseCache(max_size=10, ttl_seconds=60)
        cache.put("test query", "dataset_1", "test response")
        result = cache.get("test query", "dataset_1")
        assert result == "test response"

    def test_cache_miss(self):
        """Test cache miss."""
        cache = ResponseCache(max_size=10, ttl_seconds=60)
        result = cache.get("nonexistent", "dataset_1")
        assert result is None

    def test_cache_eviction(self):
        """Test LRU eviction."""
        cache = ResponseCache(max_size=2, ttl_seconds=60)
        cache.put("q1", "d1", "r1")
        cache.put("q2", "d1", "r2")
        cache.put("q3", "d1", "r3")  # Should evict q1
        assert cache.get("q1", "d1") is None
        assert cache.get("q2", "d1") == "r2"
