"""Application factory and lifespan management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.modules.entities.presentation.router import router as entities_router
from app.modules.health.presentation.router import router as health_router
from app.modules.observations.presentation.router import router as observations_router
from app.modules.simulation.application.simulator import simulation_manager
from app.modules.simulation.presentation.router import router as simulation_router
from app.modules.subscriptions.presentation.router import (
    router as subscriptions_router,
)
from app.shared.infrastructure.database import sessionmanager
from app.shared.infrastructure.settings import get_settings
from app.shared.infrastructure.telemetry import setup_telemetry
from app.shared.logging import configure_logging

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

    # Initialise OpenTelemetry tracing
    setup_telemetry(app, settings)

    yield

    # Graceful shutdown — stop ongoing simulations and drain DB connections
    await simulation_manager.stop()
    await sessionmanager.close()
    logger.info("database connection pool closed, application stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Urban Data API",
        description=(
            "IoT urban data ingestion service following FIWARE NGSI-v2 conventions. "
            "Modular Monolith + Clean Architecture. Benchmark workload for Aegis Platform."
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
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    # Prometheus metrics — exposed at /metrics
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/ready", "/v1/health", "/v1/ready", "/metrics"],
    ).instrument(app).expose(app)

    # Routes
    app.include_router(health_router, prefix="/v1")
    app.include_router(health_router)  # Also expose /health and /ready at root
    app.include_router(entities_router, prefix="/v1")
    app.include_router(subscriptions_router, prefix="/v1")
    app.include_router(observations_router, prefix="/v1")
    app.include_router(simulation_router, prefix="/v1")

    return app
