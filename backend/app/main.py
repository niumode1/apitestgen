"""FastAPI application factory.

Creates the FastAPI app with middleware, lifespan handlers,
and all API routers.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.config import settings
from app.database import Base, engine
from app.events import EventBus
from app.utils.logger import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    # ── Startup ──────────────────────────────────────────────
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Ensure data directories exist
    settings.data_path.mkdir(parents=True, exist_ok=True)
    (settings.data_path / "logs").mkdir(parents=True, exist_ok=True)
    settings.generated_tests_path.mkdir(parents=True, exist_ok=True)
    settings.reports_path.mkdir(parents=True, exist_ok=True)

    # Create database tables (Alembic handles migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

    # Initialize event bus
    app.state.event_bus = EventBus()
    logger.info("Event bus initialized")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("Shutting down...")
    await engine.dispose()
    logger.info("Database engine disposed")


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    app = FastAPI(
        title=f"{settings.APP_NAME} — LLM-Driven API Test Generation Platform",
        version=settings.APP_VERSION,
        description=(
            "Import OpenAPI specs, auto-generate pytest test cases via LLM agents, "
            "execute tests, and generate defect reports."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS — allow all origins in development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()
