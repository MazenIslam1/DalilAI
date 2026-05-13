"""
Dalil AI — FastAPI Application Entry Point
==========================================
Main application factory with middleware, routers, and lifecycle management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings, setup_logging
from app.db.database import close_db, init_db
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from app.routers import chat_router, datasets_router, files_router, health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Runs setup on startup and cleanup on shutdown.
    """
    # ── Startup ─────────────────────────────────────────────
    setup_logging(settings.LOG_LEVEL)

    # Create database tables
    await init_db()

    # Ensure upload/cache directories exist
    settings.upload_path
    settings.cache_path

    yield

    # ── Shutdown ────────────────────────────────────────────
    await close_db()


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI app."""

    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Dalil AI — Intelligent Business Data Analysis Engine for Tafseela. "
            "Upload CSV/Excel files and ask questions about your business data."
        ),
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Rate Limiter ────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # ── Middleware (order matters — last added = first executed) ──
    app.add_middleware(ErrorHandlerMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(files_router)
    app.include_router(chat_router)
    app.include_router(datasets_router)

    return app


# Create the app instance
app = create_app()
