"""FastAPI router for External Ingestion (Open-Meteo Public Data)."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.modules.external_ingest.application.scheduler import (
    public_data_scheduler,
)
from app.modules.external_ingest.application.use_cases.sync_public_data import (
    SyncPublicDataUseCase,
)
from app.modules.external_ingest.domain.models import (
    get_default_hcmc_stations,
)
from app.modules.external_ingest.presentation.dependencies import (
    get_sync_public_data_use_case,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/external-ingest", tags=["external-ingest"])


class StationSchema(BaseModel):
    station_id: str
    name: str
    latitude: float
    longitude: float
    entity_id: str


class SyncResponse(BaseModel):
    status: str
    stations_queried: int
    stations_updated: int
    observations_created: int
    results: list[dict[str, Any]]


@router.get(
    "/stations",
    summary="List default monitored urban stations",
    response_model=list[StationSchema],
)
async def list_stations() -> list[StationSchema]:
    """List pre-configured real-world monitoring locations across Ho Chi Minh City."""
    stations = get_default_hcmc_stations()
    return [
        StationSchema(
            station_id=s.station_id,
            name=s.name,
            latitude=s.latitude,
            longitude=s.longitude,
            entity_id=s.entity_id,
        )
        for s in stations
    ]


@router.post(
    "/sync",
    summary="Sync real-world data from Open-Meteo on demand",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
)
async def trigger_sync(
    use_case: SyncPublicDataUseCase = Depends(get_sync_public_data_use_case),
) -> SyncResponse:
    """
    Fetch real-time weather and air quality from Open-Meteo for all configured stations,
    update FIWARE entities, record time-series observations, and trigger webhook alerts.
    """
    summary = await use_case.execute()
    return SyncResponse(
        status="success",
        stations_queried=summary.stations_queried,
        stations_updated=summary.stations_updated,
        observations_created=summary.observations_created,
        results=[
            {
                "station_id": r.station_id,
                "entity_id": r.entity_id,
                "measurements": r.measurements,
            }
            for r in summary.results
        ],
    )


@router.get(
    "/status",
    summary="Get background scheduler status",
    response_model=dict[str, Any],
)
async def get_scheduler_status() -> dict[str, Any]:
    return public_data_scheduler.get_status()


@router.post(
    "/schedule/start",
    summary="Start periodic background sync from Open-Meteo",
    response_model=dict[str, Any],
)
async def start_scheduled_sync(
    interval_minutes: int = Query(
        default=10,
        ge=1,
        le=1440,
        description="Interval in minutes between Open-Meteo fetches",
    ),
) -> dict[str, Any]:
    await public_data_scheduler.start(interval_minutes=interval_minutes)
    return {
        "message": f"Periodic sync started every {interval_minutes} minutes",
        "status": public_data_scheduler.get_status(),
    }


@router.post(
    "/schedule/stop",
    summary="Stop periodic background sync",
    response_model=dict[str, Any],
)
async def stop_scheduled_sync() -> dict[str, Any]:
    await public_data_scheduler.stop()
    return {
        "message": "Periodic sync stopped",
        "status": public_data_scheduler.get_status(),
    }
