"""
Tests for File Upload Endpoints
"""

import io
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Dalil AI"


@pytest.mark.asyncio
async def test_readiness_check(client):
    """Test the readiness endpoint."""
    response = await client.get("/ready")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_csv(client, sample_csv_path):
    """Test uploading a valid CSV file."""
    with open(sample_csv_path, "rb") as f:
        response = await client.post(
            "/api/files/upload",
            files={"file": ("test_sales.csv", f, "text/csv")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "dataset_id" in data
    assert data["rows"] == 5
    assert data["columns"] == 5
    assert data["filename"] == "test_sales.csv"


@pytest.mark.asyncio
async def test_upload_invalid_extension(client):
    """Test uploading a file with invalid extension."""
    content = b"not a csv"
    response = await client.post(
        "/api/files/upload",
        files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_auth_required(client):
    """Test that endpoints require authentication."""
    # Remove the auth header
    client.headers.pop("X-API-Key", None)
    response = await client.get("/api/datasets/")
    assert response.status_code in (401, 403)
