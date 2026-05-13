"""
Rate Limiter
============
Limits API requests per client to prevent abuse.
Uses SlowAPI for FastAPI-compatible rate limiting.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import get_settings

settings = get_settings()

# Create limiter instance — uses client IP for identification
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate Limit Exceeded",
            "detail": f"Too many requests. Please wait before trying again.",
            "retry_after": str(exc.detail),
        },
    )
