"""Application factory and lifespan management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import sessionmanager

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info(
        "starting urban-data-api",
        version=settings.app_version,
        env=settings.environment,
    )

    # Initialise DB connection pool
    sessionmanager.init(settings.database_url)
    logger.info("database connection pool initialised")

    yield

    # Graceful shutdown — drain connections
    await sessionmanager.close()
    logger.info("database connection pool closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Urban Data API",
        description=(
            "IoT urban data ingestion service following FIWARE NGSI-v2 conventions. "
            "Benchmark workload for the Aegis Platform."
        ),
        version=settings.app_version,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Prometheus metrics — exposed at /metrics
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/ready", "/metrics"],
    ).instrument(app).expose(app)

    # API routes
    app.include_router(api_router, prefix="/v1")

    return app
