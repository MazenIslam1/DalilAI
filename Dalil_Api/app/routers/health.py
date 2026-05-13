"""
Health Check Router
===================
Basic health and readiness endpoints.
"""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """Basic health check — returns OK if the server is running."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check — verifies that critical dependencies are available.
    Used by Docker/Kubernetes to determine if the service can accept traffic.
    """
    checks = {
        "api_key_configured": bool(settings.GOOGLE_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
    }

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
    }
