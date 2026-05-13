"""
Global Error Handler
====================
Catches all unhandled exceptions and returns structured error responses.
"""

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns JSON error responses."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except ValueError as e:
            logger.warning("validation_error", error=str(e), path=request.url.path)
            return JSONResponse(
                status_code=400,
                content={"error": "Bad Request", "detail": str(e)},
            )

        except PermissionError as e:
            logger.warning("auth_error", error=str(e), path=request.url.path)
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "detail": str(e)},
            )

        except FileNotFoundError as e:
            logger.warning("not_found", error=str(e), path=request.url.path)
            return JSONResponse(
                status_code=404,
                content={"error": "Not Found", "detail": str(e)},
            )

        except Exception as e:
            logger.error(
                "unhandled_error",
                error=str(e),
                path=request.url.path,
                traceback=traceback.format_exc(),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred. Please try again.",
                },
            )
