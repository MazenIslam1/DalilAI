"""
Authentication Middleware
=========================
Simple API key authentication for backend protection.
Your Tafseela frontend sends the API_SECRET_KEY in the Authorization header.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

settings = get_settings()

# Expect the API key in the "X-API-Key" header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency that validates the API key.
    Use this on any router that needs protection.

    In DEBUG mode, authentication is skipped for easier local testing.

    Usage:
        @router.post("/chat", dependencies=[Depends(verify_api_key)])
    """
    # Skip auth in debug/dev mode for local testing (Swagger, etc.)
    if settings.DEBUG:
        return api_key or "debug-mode"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )

    if api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key
