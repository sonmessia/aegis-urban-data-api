"""OpenTelemetry tracing setup and instrumentation."""

import structlog
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.shared.infrastructure.settings import Settings

logger = structlog.get_logger(__name__)


def setup_telemetry(app: FastAPI, settings: Settings) -> None:
    """
    Initialize OpenTelemetry SDK with OTLP or console exporter.
    Instruments FastAPI and SQLAlchemy async engine.
    """
    resource = Resource.create(
        {
            "service.name": "urban-data-api",
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
        }
    )

    provider = TracerProvider(resource=resource)

    if settings.otel_exporter_otlp_endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_endpoint,
                insecure=True,
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(
                "opentelemetry OTLP exporter configured",
                endpoint=settings.otel_exporter_otlp_endpoint,
            )
        except Exception as exc:
            logger.warning(
                "failed to configure OTLP exporter, falling back to console",
                error=str(exc),
            )
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif settings.environment == "dev":
        # In dev without OTLP endpoint, don't flood console by default unless needed
        pass

    trace.set_tracer_provider(provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls="health,ready,metrics",
    )

    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument(tracer_provider=provider)

    logger.info("opentelemetry instrumentation completed")
