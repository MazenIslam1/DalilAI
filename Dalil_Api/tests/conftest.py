"""
Test Configuration & Shared Fixtures
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import polars as pl
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set test environment BEFORE importing app
os.environ["GOOGLE_API_KEY"] = "test_key_not_real"
os.environ["API_SECRET_KEY"] = "test_secret"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_dalil.db"
os.environ["DEBUG"] = "true"

from app.db.database import engine, init_db
from app.db.models import Base
from app.main import app


@pytest_asyncio.fixture
async def client():
    """Async test client for FastAPI."""
    # Create test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": "test_secret"},
    ) as ac:
        yield ac

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Remove test DB file
    try:
        Path("test_dalil.db").unlink(missing_ok=True)
    except Exception:
        pass


@pytest.fixture
def sample_csv_path(tmp_path) -> Path:
    """Create a sample CSV file for testing."""
    data = {
        "product": ["Widget A", "Widget B", "Widget C", "Widget A", "Widget B"],
        "sales": [100, 200, 150, 300, 250],
        "price": [10.5, 20.0, 15.5, 10.5, 20.0],
        "date": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-02-01", "2025-02-02"],
        "region": ["North", "South", "North", "South", "North"],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "test_sales.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_polars_df() -> pl.DataFrame:
    """Create a sample Polars DataFrame for testing."""
    return pl.DataFrame({
        "product": ["Widget A", "Widget B", "Widget C", "Widget A", "Widget B"],
        "sales": [100, 200, 150, 300, 250],
        "price": [10.5, 20.0, 15.5, 10.5, 20.0],
        "region": ["North", "South", "North", "South", "North"],
    })


@pytest.fixture
def sample_pandas_df() -> pd.DataFrame:
    """Create a sample Pandas DataFrame for testing."""
    return pd.DataFrame({
        "product": ["Widget A", "Widget B", "Widget C"],
        "sales": [100, 200, 150],
        "price": [10.5, 20.0, 15.5],
    })
