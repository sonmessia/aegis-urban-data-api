"""FastAPI router for IoT Simulation and Stream Generation controls."""

from typing import Any

import structlog
from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from app.modules.simulation.application.simulator import simulation_manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/simulation", tags=["simulation"])


class SimulationStatusResponse(BaseModel):
    is_running: bool
    fleet_size: int
    sample_interval_seconds: float
    metrics_emitted_total: int
    uptime_seconds: float


class SeedResponse(BaseModel):
    status: str
    seeded_count: int
    fleet_size: int


@router.get(
    "/status",
    summary="Get simulation status",
    response_model=dict[str, Any],
)
async def get_status() -> dict[str, Any]:
    return simulation_manager.get_status()


@router.post(
    "/start",
    summary="Start IoT stream simulation",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
)
async def start_simulation(
    interval_seconds: float = Query(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Seconds between sensor sweeps",
    ),
) -> dict[str, Any]:
    """
    Start continuous in-memory simulation generating realistic IoT telemetry readings
    and streaming them into the entities and observations time-series store.
    """
    # Auto-seed if not seeded
    await simulation_manager.seed_fleet()
    await simulation_manager.start(sample_interval=interval_seconds)
    return {"message": "Simulation started", "status": simulation_manager.get_status()}


@router.post(
    "/stop",
    summary="Stop IoT stream simulation",
    response_model=dict[str, Any],
)
async def stop_simulation() -> dict[str, Any]:
    await simulation_manager.stop()
    return {"message": "Simulation stopped", "status": simulation_manager.get_status()}


@router.post(
    "/seed",
    summary="Seed urban sensor fleet",
    response_model=SeedResponse,
)
async def seed_fleet() -> SeedResponse:
    """Populate default sensor entities into the database."""
    seeded = await simulation_manager.seed_fleet()
    return SeedResponse(
        status="completed",
        seeded_count=seeded,
        fleet_size=len(simulation_manager._fleet),
    )
